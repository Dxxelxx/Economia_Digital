from flask import Blueprint


produccion = Blueprint(
    "produccion",
    __name__
)


@produccion.route("/")
def mostrar_produccion():

    return """
        <h1>Producción</h1>
        <p>Módulo de producción del Taller El Obrero.</p>
    """