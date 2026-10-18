from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from sqlalchemy import or_

from database.connection import db
from models.factura import Factura
from models.pedido import Pedido
from models.cliente import Cliente


facturacion = Blueprint(
    "facturacion",
    __name__
)


# =====================================================
# VERIFICAR QUE EL USUARIO SEA ADMINISTRADOR
# =====================================================

def administrador_requerido():
    if "usuario_id" not in session:
        return redirect(
            url_for(
                "auth.login",
                next=url_for("facturacion.mostrar_facturacion")
            )
        )

    if session.get("rol") != "administrador":
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

    busqueda = request.args.get("buscar", "").strip()
    estado_filtro = request.args.get("estado", "").strip()

    consulta = (
        db.session.query(Factura)
        .join(Pedido, Factura.pedido_id == Pedido.id)
    )

    if busqueda:
        filtros = [
            Factura.numero.ilike(f"%{busqueda}%"),
            Pedido.id.cast(db.String).ilike(f"%{busqueda}%")
        ]

        if busqueda.isdigit():
            filtros.append(Factura.id == int(busqueda))

        consulta = consulta.filter(or_(*filtros))

    if estado_filtro:
        consulta = consulta.filter(
            Factura.estado_dian == estado_filtro
        )

    facturas = consulta.order_by(
        Factura.fecha.desc()
    ).all()

    total_facturas = Factura.query.count()

    facturas_pendientes = Factura.query.filter_by(
        estado_dian="PENDIENTE"
    ).count()

    facturas_aceptadas = Factura.query.filter_by(
        estado_dian="ACEPTADA"
    ).count()

    return render_template(
        "admin/facturacion.html",
        facturas=facturas,
        total_facturas=total_facturas,
        facturas_pendientes=facturas_pendientes,
        facturas_aceptadas=facturas_aceptadas,
        busqueda=busqueda,
        estado_filtro=estado_filtro
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
        "admin/detalle_factura.html",
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

    pedidos = (
        Pedido.query
        .outerjoin(
            Factura,
            Factura.pedido_id == Pedido.id
        )
        .filter(Factura.id.is_(None))
        .order_by(Pedido.fecha_pedido.desc())
        .all()
    )

    return render_template(
        "admin/pedidos_pendientes_facturacion.html",
        pedidos=pedidos
    )