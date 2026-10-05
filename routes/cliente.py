from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from models.pedido import Pedido
from models.producto import Producto


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
                next=url_for(
                    "cliente.inicio"
                )
            )
        )


    if session.get("rol") != "cliente":

        return redirect(
            url_for(
                "principal.inicio"
            )
        )


    return None


# ==========================================================
# INICIO CLIENTE
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

    # --------------------------------------
    # BUSCAR PRODUCTO
    # --------------------------------------

    producto = Producto.query.get(
        producto_id
    )


    # --------------------------------------
    # SI NO EXISTE
    # --------------------------------------

    if producto is None:

        return """
        <div style="
            font-family: Arial;
            text-align: center;
            padding: 80px;
        ">

            <h1>
                Producto no encontrado
            </h1>

            <p>
                El producto solicitado no existe
                en la base de datos.
            </p>

            <a href="/">
                Volver al catálogo
            </a>

        </div>
        """


    # --------------------------------------
    # MOSTRAR PRODUCTO
    # --------------------------------------

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


    # Solo pedidos del usuario actual
    pedidos = Pedido.query.filter_by(
        usuario_id=session["usuario_id"]
    ).all()


    return render_template(
        "mis_pedidos.html",
        pedidos=pedidos
    )


# ==========================================================
# DETALLE PEDIDO
# ==========================================================

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