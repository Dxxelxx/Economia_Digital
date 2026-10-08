from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from models.pedido import Pedido
from models.producto import Producto
from models.cliente import Cliente


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

        return redirect(
            url_for("principal.inicio")
        )

    return None


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

    producto = Producto.query.get(producto_id)

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


    # ==========================================
    # BUSCAR CLIENTE POR CORREO
    # ==========================================

    email = session.get(
        "usuario_email"
    )


    cliente_actual = Cliente.query.filter_by(
        email=email
    ).first()


    # ==========================================
    # SI TODAVÍA NO EXISTE
    # ==========================================

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

    pedido = Pedido.query.get_or_404(
        pedido_id
    )

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

    return render_template(
        "mis_facturas.html",
        facturas=[]
    )