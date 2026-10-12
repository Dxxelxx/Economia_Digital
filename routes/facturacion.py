from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash
)

from models.factura import Factura
from models.pedido import Pedido
from models.cliente import Cliente


facturacion = Blueprint(
    "facturacion",
    __name__,
    url_prefix="/facturacion"
)


# =====================================================
# VERIFICAR QUE EL USUARIO SEA ADMINISTRADOR
# =====================================================

def administrador_requerido():
    if "usuario_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("rol") != "admin":
        flash(
            "No tienes permisos para acceder a la facturación.",
            "error"
        )
        return redirect(url_for("principal.inicio"))

    return None


# =====================================================
# PANEL GENERAL DE FACTURACIÓN
# =====================================================

@facturacion.route("/")
def mostrar_facturacion():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    facturas = Factura.query.order_by(
        Factura.fecha.desc()
    ).all()

    total_facturas = len(facturas)

    facturas_pendientes = Factura.query.filter_by(
        estado_dian="PENDIENTE"
    ).count()

    facturas_aceptadas = Factura.query.filter_by(
        estado_dian="ACEPTADA"
    ).count()

    return render_template(
        "facturacion.html",
        facturas=facturas,
        total_facturas=total_facturas,
        facturas_pendientes=facturas_pendientes,
        facturas_aceptadas=facturas_aceptadas
    )


# =====================================================
# VER DETALLE DE UNA FACTURA
# =====================================================

@facturacion.route("/<int:factura_id>")
def detalle_factura(factura_id):

    acceso = administrador_requerido()

    if acceso:
        return acceso

    factura = Factura.query.get_or_404(factura_id)

    return render_template(
        "detalle_factura.html",
        factura=factura
    )


# =====================================================
# CONSULTAR PEDIDOS SIN FACTURA
# =====================================================

@facturacion.route("/pedidos-pendientes")
def pedidos_pendientes():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    pedidos = Pedido.query.filter(
        ~Pedido.id.in_(
            db.session.query(Factura.pedido_id)
        )
    ).order_by(
        Pedido.fecha_pedido.desc()
    ).all()

    return render_template(
        "pedidos_pendientes_facturacion.html",
        pedidos=pedidos
    )