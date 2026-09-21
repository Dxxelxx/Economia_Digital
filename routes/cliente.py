from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from models.pedido import Pedido


cliente = Blueprint(
    "cliente",
    __name__
)


def cliente_requerido():

    if "usuario_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    if session.get("rol") != "cliente":

        return redirect(
            url_for("admin.dashboard")
        )

    return None


# =====================================
# INICIO CLIENTE
# =====================================

@cliente.route("/")
def inicio():

    acceso = cliente_requerido()

    if acceso:

        return acceso

    return render_template(
        "cliente.html"
    )


# =====================================
# MIS PEDIDOS
# =====================================

@cliente.route("/mis-pedidos")
def mis_pedidos():

    acceso = cliente_requerido()

    if acceso:

        return acceso

    pedidos = Pedido.query.all()

    return render_template(
        "mis_pedidos.html",
        pedidos=pedidos
    )


# =====================================
# DETALLE PEDIDO
# =====================================

@cliente.route("/pedido/<int:pedido_id>")
def detalle_pedido(pedido_id):

    acceso = cliente_requerido()

    if acceso:

        return acceso

    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    return render_template(
        "detalle_pedido.html",
        pedido=pedido
    )