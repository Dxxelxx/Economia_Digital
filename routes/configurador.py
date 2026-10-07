from flask import Blueprint, render_template, session, redirect, url_for


configurador = Blueprint("configurador", __name__)


# =========================================================
# CONFIGURADOR PRINCIPAL
# =========================================================

@configurador.route("/")
def inicio():

    # Verificar que haya sesión
    if "usuario_id" not in session:
        return redirect(
            url_for(
                "auth.login",
                next=url_for("configurador.inicio")
            )
        )

    # Verificar que sea cliente
    if session.get("rol") != "cliente":
        return redirect(
            url_for("principal.inicio")
        )

    return render_template(
        "configurador.html"
    )


# =========================================================
# COMPATIBILIDAD CON cliente.html
# =========================================================

@configurador.route("/mostrar")
def mostrar_configurador():

    return redirect(
        url_for("configurador.inicio")
    )