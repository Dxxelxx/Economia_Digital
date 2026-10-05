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


# ==========================================================
# LOGIN
# ==========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        next_page = request.form.get("next", "").strip()


        # ------------------------------------------
        # VALIDACIÓN
        # ------------------------------------------

        if not username or not password:

            flash(
                "Por favor completa todos los campos.",
                "error"
            )

            return render_template(
                "login.html",
                next=next_page
            )


        # ------------------------------------------
        # BUSCAR USUARIO
        # ------------------------------------------

        usuario = Usuario.query.filter_by(
            username=username
        ).first()


        # ------------------------------------------
        # COMPROBAR CONTRASEÑA
        # ------------------------------------------

        if usuario and usuario.verificar_password(password):

            session["usuario_id"] = usuario.id
            session["usuario_nombre"] = usuario.nombre
            session["usuario_username"] = usuario.username
            session["rol"] = usuario.rol


            # Administrador
            if usuario.rol == "administrador":

                return redirect(
                    url_for("admin.dashboard")
                )


            # Si venía desde otra página
            if next_page:

                return redirect(next_page)


            # Cliente
            return redirect(
                url_for("cliente.inicio")
            )


        # ------------------------------------------
        # LOGIN INCORRECTO
        # ------------------------------------------

        flash(
            "Usuario o contraseña incorrectos.",
            "error"
        )

        return render_template(
            "login.html",
            next=next_page
        )


    # ------------------------------------------
    # GET
    # ------------------------------------------

    next_page = request.args.get(
        "next",
        ""
    )


    return render_template(
        "login.html",
        next=next_page
    )


# ==========================================================
# REGISTRO
# ==========================================================

@auth.route("/registro", methods=["GET", "POST"])
def registro():

    next_page = request.args.get(
        "next",
        ""
    )


    # ======================================================
    # GET
    # ======================================================

    if request.method == "GET":

        return render_template(
            "registro.html",
            next=next_page
        )


    # ======================================================
    # POST
    # ======================================================

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


    # Por compatibilidad
    if not email:

        email = request.form.get(
            "correo",
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


    # ------------------------------------------
    # NEXT
    # ------------------------------------------

    next_form = request.form.get(
        "next",
        ""
    ).strip()


    if next_form:

        next_page = next_form


    # ======================================================
    # VALIDACIONES
    # ======================================================

    if not nombre:

        flash(
            "Debes ingresar tu nombre completo.",
            "error"
        )

        return render_template(
            "registro.html",
            next=next_page
        )


    if not username:

        flash(
            "Debes ingresar un nombre de usuario.",
            "error"
        )

        return render_template(
            "registro.html",
            next=next_page
        )


    if not email:

        flash(
            "Debes ingresar tu correo electrónico.",
            "error"
        )

        return render_template(
            "registro.html",
            next=next_page
        )


    if not password:

        flash(
            "Debes ingresar una contraseña.",
            "error"
        )

        return render_template(
            "registro.html",
            next=next_page
        )


    if password != confirmar_password:

        flash(
            "Las contraseñas no coinciden.",
            "error"
        )

        return render_template(
            "registro.html",
            next=next_page
        )


    # ======================================================
    # COMPROBAR EXISTENCIA
    # ======================================================

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


        return render_template(
            "registro.html",
            next=next_page
        )


    # ======================================================
    # CREAR USUARIO
    # ======================================================

    usuario = Usuario(
        nombre=nombre,
        username=username,
        email=email,
        rol="cliente"
    )


    usuario.establecer_password(
        password
    )


    # ======================================================
    # GUARDAR
    # ======================================================

    try:

        db.session.add(usuario)

        db.session.commit()


    except Exception as error:

        db.session.rollback()

        print(
            "===================================="
        )

        print(
            "ERROR REGISTRANDO USUARIO:"
        )

        print(
            error
        )

        print(
            "===================================="
        )

        flash(
            "No se pudo crear la cuenta.",
            "error"
        )

        return render_template(
            "registro.html",
            next=next_page
        )


    # ======================================================
    # SESIÓN AUTOMÁTICA
    # ======================================================

    session["usuario_id"] = usuario.id
    session["usuario_nombre"] = usuario.nombre
    session["usuario_username"] = usuario.username
    session["rol"] = "cliente"


    flash(
        f"¡Bienvenido, {usuario.nombre}!",
        "success"
    )


    # ======================================================
    # REDIRECCIÓN
    # ======================================================

    if next_page:

        return redirect(
            next_page
        )


    return redirect(
        url_for(
            "cliente.inicio"
        )
    )


# ==========================================================
# LOGOUT
# ==========================================================

@auth.route("/logout")
def logout():

    session.clear()

    flash(
        "Sesión cerrada correctamente.",
        "success"
    )

    return redirect(
        url_for(
            "principal.inicio"
        )
    )