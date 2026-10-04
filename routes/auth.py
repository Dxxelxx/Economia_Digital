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

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Validar campos
        if not username or not password:

            flash(
                "Por favor completa todos los campos.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )

        # Buscar usuario
        usuario = Usuario.query.filter_by(
            username=username
        ).first()

        # Verificar usuario y contraseña
        if usuario and usuario.verificar_password(password):

            session["usuario_id"] = usuario.id
            session["usuario_nombre"] = usuario.nombre
            session["rol"] = usuario.rol

            # Si es administrador
            if usuario.rol == "administrador":

                return redirect(
                    url_for("admin.dashboard")
                )

            # Si es cliente
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

        # =================================
        # OBTENER DATOS DEL FORMULARIO
        # =================================

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirmar_password = request.form.get(
            "confirmar_password",
            ""
        )


        # =================================
        # VALIDAR CAMPOS
        # =================================

        if not nombre:

            flash(
                "Debes ingresar tu nombre completo.",
                "error"
            )

            return redirect(
                url_for("auth.registro")
            )


        if not username:

            flash(
                "Debes ingresar un nombre de usuario.",
                "error"
            )

            return redirect(
                url_for("auth.registro")
            )


        if not email:

            flash(
                "Debes ingresar tu correo electrónico.",
                "error"
            )

            return redirect(
                url_for("auth.registro")
            )


        if not password:

            flash(
                "Debes ingresar una contraseña.",
                "error"
            )

            return redirect(
                url_for("auth.registro")
            )


        # =================================
        # CONFIRMAR CONTRASEÑA
        # =================================

        if password != confirmar_password:

            flash(
                "Las contraseñas no coinciden.",
                "error"
            )

            return redirect(
                url_for("auth.registro")
            )


        # =================================
        # VERIFICAR USUARIO EXISTENTE
        # =================================

        usuario_existente = Usuario.query.filter(
            (Usuario.username == username) |
            (Usuario.email == email)
        ).first()


        if usuario_existente:

            if usuario_existente.username == username:

                flash(
                    "Ese nombre de usuario ya está registrado.",
                    "error"
                )

            else:

                flash(
                    "Ese correo electrónico ya está registrado.",
                    "error"
                )

            return redirect(
                url_for("auth.registro")
            )


        # =================================
        # CREAR USUARIO
        # =================================

        usuario = Usuario(

            nombre=nombre,

            username=username,

            email=email,

            rol="cliente"

        )


        # =================================
        # ENCRIPTAR CONTRASEÑA
        # =================================

        usuario.establecer_password(
            password
        )


        # =================================
        # GUARDAR EN POSTGRESQL
        # =================================

        try:

            db.session.add(
                usuario
            )

            db.session.commit()

        except Exception as error:

            db.session.rollback()

            print(
                "ERROR AL REGISTRAR USUARIO:",
                error
            )

            flash(
                "Ocurrió un error al crear la cuenta. Inténtalo nuevamente.",
                "error"
            )

            return redirect(
                url_for("auth.registro")
            )


        # =================================
        # REGISTRO EXITOSO
        # =================================

        flash(
            "Cuenta creada correctamente. Ahora puedes iniciar sesión.",
            "success"
        )


        return redirect(
            url_for("auth.login")
        )


    return render_template(
        "registro.html"
    )


# =====================================
# LOGOUT
# =====================================

@auth.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("principal.inicio")
    )