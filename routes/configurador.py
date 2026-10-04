from flask import Blueprint, render_template

configurador = Blueprint("configurador", __name__)


@configurador.route("/")
def inicio():
    return render_template("configurador.html")