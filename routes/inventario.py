from flask import Blueprint


inventario = Blueprint(
    "inventario",
    __name__
)


@inventario.route("/")
def mostrar_inventario():

    return """
        <h1>Inventario</h1>
        <p>Módulo de inventario del Taller El Obrero.</p>
    """