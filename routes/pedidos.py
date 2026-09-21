from flask import Blueprint


pedidos = Blueprint(
    "pedidos",
    __name__
)


@pedidos.route("/")
def mostrar_pedidos():

    return """
        <h1>Pedidos</h1>
        <p>Módulo de pedidos del Taller El Obrero.</p>
    """