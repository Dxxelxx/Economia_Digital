from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)


# =========================================
# BLUEPRINT CONFIGURADOR
# =========================================

configurador = Blueprint(
    "configurador",
    __name__
)


# =========================================
# PÁGINA DEL CONFIGURADOR
# =========================================

@configurador.route("/")
def inicio():

    # -------------------------------------
    # VERIFICAR SI EL USUARIO INICIÓ SESIÓN
    # -------------------------------------

    if "usuario_id" not in session:

        return redirect(
            url_for(
                "auth.login",
                next=url_for(
                    "configurador.inicio"
                )
            )
        )


    # -------------------------------------
    # VERIFICAR QUE SEA CLIENTE
    # -------------------------------------

    if session.get("rol") != "cliente":

        return redirect(
            url_for(
                "principal.inicio"
            )
        )


    # -------------------------------------
    # MOSTRAR CONFIGURADOR
    # -------------------------------------

    return render_template(
        "configurador.html"
    )