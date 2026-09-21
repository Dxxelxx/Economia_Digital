from flask import Blueprint, render_template


configurador = Blueprint(
    "configurador",
    __name__
)


@configurador.route("/")
def mostrar_configurador():

    return render_template(
        "configurador.html"
    )