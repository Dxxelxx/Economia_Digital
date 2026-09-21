from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database.connection import db
from models.usuario import Usuario


auth = Blueprint("auth", __name__)


# =====================================
# LOGIN
# =====================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        usuario = Usuario.query.filter_by(
            username=username
        ).first()

        if usuario and usuario.verificar_password(password):

            session["usuario_id"] = usuario.id
            session["usuario_nombre"] = usuario.nombre
            session["rol"] = usuario.rol

            if usuario.rol == "administrador":
                return redirect(
                    url_for("admin.dashboard")
                )

            return redirect(
                url_for("cliente.inicio")
            )

        flash(
            "Usuario o contraseña incorrectos.",
            "error"
        )

    return render_template("login.html")


# =====================================
# REGISTRO
# =====================================

@auth.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form.get("nombre")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        usuario_existente = Usuario.query.filter(
            (Usuario.username == username) |
            (Usuario.email == email)
        ).first()

        if usuario_existente:

            flash(
                "El usuario o correo ya existe.",
                "error"
            )

            return redirect(
                url_for("auth.registro")
            )

        usuario = Usuario(
            nombre=nombre,
            username=username,
            email=email,
            rol="cliente"
        )

        usuario.establecer_password(password)

        db.session.add(usuario)
        db.session.commit()

        flash(
            "Cuenta creada correctamente.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template("registro.html")


# =====================================
# LOGOUT
# =====================================

@auth.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("principal.inicio")
    )