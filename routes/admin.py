from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from sqlalchemy import func
from datetime import datetime, timedelta

from database.connection import db
from models.pedido import Pedido
from models.cliente import Cliente
from models.producto import Producto


admin = Blueprint("admin", __name__)


# =========================================================
# ESTADOS PERMITIDOS
# =========================================================

ESTADOS_PEDIDO = [
    "Pendiente",
    "Aceptado",
    "En producción",
    "Listo para enviar",
    "Enviado",
    "Entregado",
    "Cancelado"
]


# =========================================================
# FLUJO NORMAL DE LOS PEDIDOS
# =========================================================

FLUJO_PEDIDO = {
    "Pendiente": [
        "Aceptado",
        "Cancelado"
    ],

    "Aceptado": [
        "En producción",
        "Cancelado"
    ],

    "En producción": [
        "Listo para enviar",
        "Cancelado"
    ],

    "Listo para enviar": [
        "Enviado",
        "Cancelado"
    ],

    "Enviado": [
        "Entregado"
    ],

    "Entregado": [],

    "Cancelado": []
}


# =========================================================
# VERIFICAR ACCESO DEL ADMINISTRADOR
# =========================================================

def administrador_requerido():

    if "usuario_id" not in session:

        return redirect(
            url_for(
                "auth.login",
                next=url_for("admin.dashboard")
            )
        )

    if session.get("rol") != "administrador":

        flash(
            "No tienes permisos para acceder al administrador.",
            "error"
        )

        if session.get("rol") == "cliente":

            return redirect(
                url_for("cliente.inicio")
            )

        return redirect(
            url_for("auth.login")
        )

    return None


# =========================================================
# PANEL PRINCIPAL
# =========================================================

@admin.route("/")
def dashboard():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    total_pedidos = Pedido.query.count()

    total_productos = Producto.query.filter_by(
        activo=True
    ).count()

    pedidos_pendientes = Pedido.query.filter_by(
        estado="Pendiente"
    ).count()

    ventas_registradas = db.session.query(
        func.coalesce(
            func.sum(Pedido.total),
            0
        )
    ).filter(
        Pedido.estado != "Cancelado"
    ).scalar()

    pedidos_recientes = Pedido.query.order_by(
        Pedido.fecha_pedido.desc()
    ).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        total_pedidos=total_pedidos,
        total_productos=total_productos,
        pedidos_pendientes=pedidos_pendientes,
        ventas_registradas=ventas_registradas,
        pedidos_recientes=pedidos_recientes
    )


# =========================================================
# LISTADO DE PEDIDOS
# =========================================================

@admin.route("/pedidos")
def pedidos():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    estado_filtro = request.args.get(
        "estado",
        ""
    ).strip()

    busqueda = request.args.get(
        "buscar",
        ""
    ).strip()

    consulta = Pedido.query

    # Filtrar por estado.
    if estado_filtro in ESTADOS_PEDIDO:

        consulta = consulta.filter(
            Pedido.estado == estado_filtro
        )

    # Buscar por número de pedido.
    if busqueda:

        if busqueda.isdigit():

            consulta = consulta.filter(
                Pedido.id == int(busqueda)
            )

        else:

            flash(
                "Para buscar un pedido, introduce su número.",
                "info"
            )

    pedidos_registrados = consulta.order_by(
        Pedido.fecha_pedido.desc()
    ).all()

    return render_template(
        "admin/pedidos.html",
        pedidos=pedidos_registrados,
        estados_pedido=ESTADOS_PEDIDO,
        estado_filtro=estado_filtro,
        busqueda=busqueda,
        flujo_pedido=FLUJO_PEDIDO
    )


# =========================================================
# DETALLE DE UN PEDIDO
# =========================================================

@admin.route("/pedidos/<int:pedido_id>")
def detalle_pedido(pedido_id):

    acceso = administrador_requerido()

    if acceso:
        return acceso

    pedido = db.session.get(Pedido, pedido_id)

    if pedido is None:

        flash(
            "El pedido solicitado no existe.",
            "error"
        )

        return redirect(url_for("admin.pedidos"))

    return render_template(
        "admin/detalle_pedido.html",
        pedido=pedido
    )


# =========================================================
# ACTUALIZAR ESTADO DEL PEDIDO
# =========================================================

@admin.route(
    "/pedidos/<int:pedido_id>/estado",
    methods=["POST"]
)
def actualizar_estado_pedido(pedido_id):

    acceso = administrador_requerido()

    if acceso:
        return acceso

    pedido = db.session.get(
        Pedido,
        pedido_id
    )

    if pedido is None:

        flash(
            "El pedido solicitado no existe.",
            "error"
        )

        return redirect(
            url_for("admin.pedidos")
        )

    nuevo_estado = request.form.get(
        "estado",
        ""
    ).strip()

    estado_anterior = pedido.estado

    # Validar el estado solicitado.
    if nuevo_estado not in ESTADOS_PEDIDO:

        flash(
            "El estado seleccionado no es válido.",
            "error"
        )

        return redirect(
            url_for("admin.pedidos")
        )

    # Evitar repetir el mismo estado.
    if estado_anterior == nuevo_estado:

        flash(
            "El pedido ya tiene ese estado.",
            "info"
        )

        return redirect(
            url_for("admin.pedidos")
        )

    # Comprobar que la transición esté permitida.
    estados_siguientes = FLUJO_PEDIDO.get(
        estado_anterior,
        []
    )

    if nuevo_estado not in estados_siguientes:

        flash(
            f"No se puede cambiar un pedido de "
            f"'{estado_anterior}' a '{nuevo_estado}'.",
            "error"
        )

        return redirect(
            url_for("admin.pedidos")
        )

    try:

        # Actualizar estado.
        pedido.estado = nuevo_estado

        # Establecer fecha estimada cuando se acepta.
        if (
            nuevo_estado == "Aceptado"
            and pedido.fecha_entrega is None
        ):

            pedido.fecha_entrega = (
                datetime.utcnow() + timedelta(days=5)
            ).date()

        db.session.commit()

        flash(
            f"El pedido #{pedido.id:05d} cambió de "
            f"'{estado_anterior}' a '{nuevo_estado}'.",
            "success"
        )

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR AL ACTUALIZAR PEDIDO:",
            error
        )

        flash(
            "No fue posible actualizar el pedido. "
            "Inténtalo nuevamente.",
            "error"
        )

    return redirect(
        url_for("admin.pedidos")
    )


# =========================================================
# INVENTARIO, PRODUCCIÓN Y FACTURACIÓN
# Estas secciones tienen su propio módulo; aquí solo se
# redirige para que los enlaces del panel funcionen.
# =========================================================

@admin.route("/inventario")
def inventario():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return redirect(url_for("inventario.mostrar_inventario"))


@admin.route("/produccion")
def produccion():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return redirect(url_for("produccion.mostrar_produccion"))


@admin.route("/facturacion")
def facturacion():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return redirect(url_for("facturacion.mostrar_facturacion"))