from flask import Blueprint


facturacion = Blueprint(
    "facturacion",
    __name__
)


@facturacion.route("/")
def mostrar_facturacion():

    return """
        <h1>Facturación</h1>
        <p>Módulo de facturación del Taller El Obrero.</p>
    """