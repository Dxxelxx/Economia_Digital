from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from sqlalchemy import func

from database.connection import db
from models.pedido import Pedido
from models.producto import Producto


admin = Blueprint("admin", __name__)


# =====================================================
# VERIFICAR ACCESO DEL ADMINISTRADOR
# =====================================================

def administrador_requerido():

    if "usuario_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    if session.get("rol") != "administrador":
        return redirect(
            url_for("cliente.inicio")
        )

    return None


# =====================================================
# DASHBOARD PRINCIPAL
# =====================================================

@admin.route("/")
def dashboard():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    # ---------------------------------------------
    # TOTAL DE PEDIDOS
    # ---------------------------------------------

    total_pedidos = (
        db.session.query(func.count(Pedido.id))
        .scalar()
        or 0
    )

    # ---------------------------------------------
    # TOTAL DE PRODUCTOS ACTIVOS
    # ---------------------------------------------

    total_productos = (
        Producto.query
        .filter_by(activo=True)
        .count()
    )

    # ---------------------------------------------
    # PEDIDOS PENDIENTES
    # ---------------------------------------------

    pedidos_pendientes = (
        Pedido.query
        .filter_by(estado="Pendiente")
        .count()
    )

    # ---------------------------------------------
    # VENTAS REGISTRADAS
    # ---------------------------------------------
    # Por ahora se suma el total de los pedidos
    # que no estén cancelados.
    #
    # Esto representa el valor de los pedidos
    # registrados, no necesariamente dinero cobrado.

    ventas_registradas = (
        db.session.query(
            func.coalesce(func.sum(Pedido.total), 0)
        )
        .filter(Pedido.estado != "Cancelado")
        .scalar()
    )

    # ---------------------------------------------
    # PEDIDOS RECIENTES
    # ---------------------------------------------

    pedidos_recientes = (
        Pedido.query
        .order_by(Pedido.fecha_pedido.desc())
        .limit(5)
        .all()
    )

    # ---------------------------------------------
    # RENDERIZAR DASHBOARD
    # ---------------------------------------------

    return render_template(
        "admin/dashboard.html",
        total_pedidos=total_pedidos,
        total_productos=total_productos,
        pedidos_pendientes=pedidos_pendientes,
        ventas_registradas=ventas_registradas,
        pedidos_recientes=pedidos_recientes
    )


# =====================================================
# INVENTARIO
# =====================================================

@admin.route("/inventario")
def inventario():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/inventario.html"
    )


# =====================================================
# PEDIDOS
# =====================================================

@admin.route("/pedidos")
def pedidos():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/pedidos.html"
    )


# =====================================================
# PRODUCCIÓN
# =====================================================

@admin.route("/produccion")
def produccion():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/produccion.html"
    )


# =====================================================
# FACTURACIÓN
# =====================================================

@admin.route("/facturacion")
def facturacion():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/facturacion.html"
    )