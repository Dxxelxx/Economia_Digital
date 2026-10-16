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
# ESTADOS PERMITIDOS PARA LOS PEDIDOS
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
# VERIFICAR ACCESO DEL ADMINISTRADOR
# =========================================================

def administrador_requerido():

    if "usuario_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("rol") != "administrador":
        flash(
            "No tienes permisos para acceder al administrador.",
            "error"
        )
        return redirect(url_for("principal.inicio"))

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
        func.coalesce(func.sum(Pedido.total), 0)
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

    estado_filtro = request.args.get("estado", "").strip()

    consulta = Pedido.query

    if estado_filtro in ESTADOS_PEDIDO:
        consulta = consulta.filter_by(
            estado=estado_filtro
        )

    pedidos_registrados = consulta.order_by(
        Pedido.fecha_pedido.desc()
    ).all()

    return render_template(
        "admin/pedidos.html",
        pedidos=pedidos_registrados,
        estados_pedido=ESTADOS_PEDIDO,
        estado_filtro=estado_filtro
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

    pedido = Pedido.query.get_or_404(pedido_id)

    nuevo_estado = request.form.get(
        "estado",
        ""
    ).strip()

    if nuevo_estado not in ESTADOS_PEDIDO:
        flash(
            "El estado seleccionado no es válido.",
            "error"
        )

        return redirect(
            url_for("admin.pedidos")
        )

    estado_anterior = pedido.estado

    # No realizar cambios innecesarios.
    if estado_anterior == nuevo_estado:
        flash(
            "El pedido ya tiene ese estado.",
            "info"
        )

        return redirect(
            url_for("admin.pedidos")
        )

    try:

        pedido.estado = nuevo_estado

        # Si se confirma o inicia la fabricación,
        # calculamos una fecha estimada de entrega
        # solamente cuando todavía no existe.
        if (
            nuevo_estado in [
                "Aceptado",
                "En producción"
            ]
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
            "ERROR AL ACTUALIZAR EL ESTADO DEL PEDIDO:",
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
# INVENTARIO
# =========================================================

@admin.route("/inventario")
def inventario():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/inventario.html"
    )


# =========================================================
# PRODUCCIÓN
# =========================================================

@admin.route("/produccion")
def produccion():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/produccion.html"
    )


# =========================================================
# FACTURACIÓN
# =========================================================

@admin.route("/facturacion")
def facturacion():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/facturacion.html"
    )