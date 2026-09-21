from flask import Blueprint


dashboard = Blueprint(
    "dashboard",
    __name__
)


@dashboard.route("/")
def mostrar_dashboard():

    return """
        <h1>Dashboard</h1>
        <p>Panel administrativo del Taller El Obrero.</p>
    """