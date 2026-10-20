from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    flash
)

from database.connection import db

from models.pedido import Pedido
from models.producto import Producto
from models.cliente import Cliente
from models.factura import Factura
from flask import send_file
from utils.generar_factura_pdf import generar_factura_pdf


cliente = Blueprint(
    "cliente",
    __name__
)


# ==========================================================
# VERIFICAR CLIENTE
# ==========================================================

def cliente_requerido():

    if "usuario_id" not in session:

        return redirect(
            url_for(
                "auth.login",
                next=url_for("cliente.inicio")
            )
        )

    if session.get("rol") != "cliente":

        flash(
            "No tienes permisos para acceder a esta sección.",
            "error"
        )

        return redirect(
            url_for("principal.inicio")
        )

    return None


# ==========================================================
# BUSCAR CLIENTE ASOCIADO A LA SESIÓN
# ==========================================================

def obtener_cliente_actual():

    email = (
        session.get("usuario_email") or ""
    ).strip().lower()

    if not email:
        return None

    return Cliente.query.filter(
        db.func.lower(Cliente.email) == email
    ).first()


# ==========================================================
# INICIO DEL CLIENTE
# ==========================================================

@cliente.route("/")
def inicio():

    acceso = cliente_requerido()

    if acceso:
        return acceso

    return render_template(
        "cliente.html"
    )


# ==========================================================
# VER PRODUCTO
# ==========================================================

@cliente.route("/producto/<int:producto_id>")
def producto(producto_id):

    producto = Producto.query.get_or_404(
        producto_id
    )

    return render_template(
        "producto.html",
        producto=producto
    )


# ==========================================================
# MIS PEDIDOS
# ==========================================================

@cliente.route("/mis-pedidos")
def mis_pedidos():

    acceso = cliente_requerido()

    if acceso:
        return acceso

    cliente_actual = obtener_cliente_actual()

    if cliente_actual is None:

        pedidos = []

    else:

        pedidos = Pedido.query.filter_by(
            cliente_id=cliente_actual.id
        ).order_by(
            Pedido.fecha_pedido.desc()
        ).all()

    return render_template(
        "mis_pedidos.html",
        pedidos=pedidos
    )


# ==========================================================
# DETALLE DEL PEDIDO
# ==========================================================

@cliente.route("/pedido/<int:pedido_id>")
def detalle_pedido(pedido_id):

    acceso = cliente_requerido()

    if acceso:
        return acceso

    cliente_actual = obtener_cliente_actual()

    if cliente_actual is None:

        flash(
            "No se encontró tu registro de cliente.",
            "error"
        )

        return redirect(
            url_for("cliente.mis-pedidos")
        )

    pedido = Pedido.query.filter_by(
        id=pedido_id,
        cliente_id=cliente_actual.id
    ).first_or_404()

    return render_template(
        "detalle_pedido.html",
        pedido=pedido
    )


# ==========================================================
# MIS FACTURAS
# ==========================================================

@cliente.route("/mis-facturas")
def mis_facturas():

    acceso = cliente_requerido()

    if acceso:
        return acceso

    cliente_actual = obtener_cliente_actual()

    # No mostrar facturas si no existe un cliente asociado.
    if cliente_actual is None:

        facturas = []

    else:

        # Solo consultar las facturas de los pedidos
        # que pertenecen al cliente autenticado.
        facturas = (
            Factura.query
            .join(
                Pedido,
                Factura.pedido_id == Pedido.id
            )
            .filter(
                Pedido.cliente_id == cliente_actual.id
            )
            .order_by(
                Factura.fecha.desc()
            )
            .all()
        )

    return render_template(
        "mis_facturas.html",
        facturas=facturas
    )

@cliente.route("/mis-facturas/<int:factura_id>/pdf")
def descargar_mi_factura_pdf(factura_id):
    acceso = cliente_requerido()

    if acceso:
        return acceso

    cliente_actual = obtener_cliente_actual()

    if cliente_actual is None:
        flash("No se encontró tu registro de cliente.", "error")
        return redirect(url_for("cliente.mis_facturas"))

    factura = (
        Factura.query
        .join(Pedido, Factura.pedido_id == Pedido.id)
        .filter(
            Factura.id == factura_id,
            Pedido.cliente_id == cliente_actual.id
        )
        .first_or_404()
    )

    archivo = generar_factura_pdf(factura)

    return send_file(
        archivo,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"factura_{factura.numero}.pdf"
    )