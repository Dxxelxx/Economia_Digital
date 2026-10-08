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
from models.cliente import Cliente

auth = Blueprint("auth", __name__)


# =========================================================
# LOGIN
# =========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    siguiente = request.args.get("next", "")

    if request.method == "POST":

        identificador = (
            request.form.get("username")
            or request.form.get("correo")
            or request.form.get("email")
            or ""
        ).strip()

        password = request.form.get("password", "")

        siguiente = request.form.get("next") or siguiente or ""

        # Validar usuario/correo
        if not identificador:
            flash("Debes ingresar tu usuario o correo.", "error")
            return render_template(
                "login.html",
                next=siguiente
            )

        # Validar contraseña
        if not password:
            flash("Debes ingresar tu contraseña.", "error")
            return render_template(
                "login.html",
                next=siguiente
            )

        # Buscar usuario por username o correo
        usuario = Usuario.query.filter(
            (Usuario.username == identificador) |
            (Usuario.email == identificador.lower())
        ).first()

        # Verificar contraseña
        if usuario and usuario.verificar_password(password):

            session.clear()

            session["usuario_id"] = usuario.id
            session["usuario_nombre"] = usuario.nombre
            session["usuario_username"] = usuario.username
            session["usuario_email"] = usuario.email
            session["rol"] = usuario.rol

            # Administrador
            if usuario.rol == "administrador":
                return redirect(
                    url_for("admin.dashboard")
                )

            # Si venía desde otra página
            if siguiente:
                return redirect(siguiente)

            # Cliente
            return redirect(
                url_for("cliente.inicio")
            )

        flash(
            "Usuario/correo o contraseña incorrectos.",
            "error"
        )

        return render_template(
            "login.html",
            next=siguiente
        )

    # IMPORTANTE:
    # Esto soluciona el error del GET /auth/login
    return render_template(
        "login.html",
        next=siguiente
    )


# =========================================================
# REGISTRO
# =========================================================

@auth.route("/registro", methods=["GET", "POST"])
def registro():

    siguiente = request.args.get("next", "")

    if request.method == "POST":

        # ==========================================
        # DATOS DEL FORMULARIO
        # ==========================================

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = (
            request.form.get("email")
            or request.form.get("correo")
            or ""
        ).strip().lower()

        documento = request.form.get(
            "documento",
            ""
        ).strip()

        telefono = request.form.get(
            "telefono",
            ""
        ).strip()

        direccion = request.form.get(
            "direccion",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirmar_password = request.form.get(
            "confirmar_password",
            ""
        )

        siguiente = (
            request.form.get("next")
            or siguiente
            or ""
        )


        # ==========================================
        # VALIDACIONES
        # ==========================================

        if not nombre:

            flash(
                "Debes ingresar tu nombre completo.",
                "error"
            )

            return render_template(
                "registro.html",
                next=siguiente
            )


        if not email:

            flash(
                "Debes ingresar tu correo electrónico.",
                "error"
            )

            return render_template(
                "registro.html",
                next=siguiente
            )


        if not password:

            flash(
                "Debes ingresar una contraseña.",
                "error"
            )

            return render_template(
                "registro.html",
                next=siguiente
            )


        if password != confirmar_password:

            flash(
                "Las contraseñas no coinciden.",
                "error"
            )

            return render_template(
                "registro.html",
                next=siguiente
            )


        if len(password) < 6:

            flash(
                "La contraseña debe tener al menos 6 caracteres.",
                "error"
            )

            return render_template(
                "registro.html",
                next=siguiente
            )


        # ==========================================
        # GENERAR USUARIO AUTOMÁTICAMENTE
        # ==========================================

        if not username:

            base_username = email.split("@")[0]

            username = base_username

            contador = 1

            while Usuario.query.filter_by(
                username=username
            ).first():

                username = (
                    f"{base_username}{contador}"
                )

                contador += 1


        # ==========================================
        # VERIFICAR USUARIO EXISTENTE
        # ==========================================

        usuario_existente = Usuario.query.filter(
            (Usuario.username == username)
            |
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
                next=siguiente
            )


        # ==========================================
        # CREAR USUARIO
        # ==========================================

        usuario = Usuario(
            nombre=nombre,
            username=username,
            email=email,
            rol="cliente"
        )

        usuario.establecer_password(
            password
        )


        # ==========================================
        # GUARDAR USUARIO
        # ==========================================

        try:

            db.session.add(usuario)

            db.session.flush()


            # ======================================
            # CREAR CLIENTE
            # ======================================

            cliente = Cliente(
                nombre=nombre,
                documento=documento if documento else None,
                telefono=telefono if telefono else None,
                email=email,
                direccion=direccion if direccion else None
            )

            db.session.add(cliente)

            db.session.commit()


        except Exception as error:

            db.session.rollback()

            print(
                "ERROR AL REGISTRAR USUARIO/CLIENTE:"
            )

            print(error)

            flash(
                "No se pudo crear la cuenta. "
                "Revisa los datos e inténtalo nuevamente.",
                "error"
            )

            return render_template(
                "registro.html",
                next=siguiente
            )


        # ==========================================
        # CREAR SESIÓN
        # ==========================================

        session.clear()

        session["usuario_id"] = usuario.id

        session["usuario_nombre"] = usuario.nombre

        session["usuario_username"] = usuario.username

        session["usuario_email"] = usuario.email

        session["rol"] = usuario.rol


        # ==========================================
        # REDIRECCIÓN
        # ==========================================

        if siguiente:

            return redirect(siguiente)

        return redirect(
            url_for("cliente.inicio")
        )

    # =====================================================
    # IMPORTANTE:
    # CUANDO ENTRAMOS DIRECTAMENTE A /auth/registro
    # =====================================================

    return render_template(
        "registro.html",
        next=siguiente
    )


# =========================================================
# CERRAR SESIÓN
# =========================================================

@auth.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("principal.inicio")
    )