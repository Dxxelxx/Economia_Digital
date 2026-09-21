from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)


admin = Blueprint("admin", __name__)


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


# =====================================
# DASHBOARD
# =====================================

@admin.route("/")
def dashboard():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/dashboard.html"
    )


# =====================================
# INVENTARIO
# =====================================

@admin.route("/inventario")
def inventario():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/inventario.html"
    )


# =====================================
# PEDIDOS
# =====================================

@admin.route("/pedidos")
def pedidos():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/pedidos.html"
    )


# =====================================
# PRODUCCIÓN
# =====================================

@admin.route("/produccion")
def produccion():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/produccion.html"
    )


# =====================================
# FACTURACIÓN
# =====================================

@admin.route("/facturacion")
def facturacion():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    return render_template(
        "admin/facturacion.html"
    )