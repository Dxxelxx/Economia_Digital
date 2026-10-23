from decimal import Decimal

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from database.connection import db

from models.cliente import Cliente

from servicies.configurador_service import (
    PRODUCTOS,
    IVA,
    catalogo_para_cliente,
    describir_diseno,
    nombre_de_color,
    validar_diseno
)

from servicies.pedido_service import crear_pedido_desde_diseno


configurador = Blueprint("configurador", __name__)


# =========================================================
# AYUDAS
# =========================================================

def es_cliente():
    return (
        "usuario_id" in session
        and session.get("rol") == "cliente"
    )


def obtener_cliente_actual():

    email = (session.get("usuario_email") or "").strip().lower()

    if not email:
        return None

    return Cliente.query.filter(
        db.func.lower(Cliente.email) == email
    ).first()


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
        "configurador.html",
        catalogo=catalogo_para_cliente()
    )


# =========================================================
# GUARDAR EL DISEÑO (lo llama el botón "Comprar este diseño")
# =========================================================

@configurador.route("/diseno", methods=["POST"])
def guardar_diseno():

    if not es_cliente():
        return jsonify({
            "ok": False,
            "mensaje": "Inicia sesión como cliente para comprar tu diseño.",
            "redirigir": url_for(
                "auth.login",
                next=url_for("configurador.inicio")
            )
        }), 401

    diseno, error = validar_diseno(request.get_json(silent=True))

    if error:
        return jsonify({"ok": False, "mensaje": error}), 400

    # Se guarda en la sesión; el precio se recalculó en el servidor.
    session["diseno_pendiente"] = diseno

    return jsonify({
        "ok": True,
        "redirigir": url_for("configurador.confirmar")
    })


# =========================================================
# CONFIRMAR LA COMPRA DEL DISEÑO
# =========================================================

def datos_para_confirmar(diseno, cantidad=1):

    producto = PRODUCTOS[diseno["producto"]]
    textos = describir_diseno(diseno)

    return {
        "diseno": diseno,
        "producto": producto,
        "textos": textos,
        "nombre_color": nombre_de_color(diseno["color"]),
        "nombre_color_secundario": nombre_de_color(diseno["colorSecundario"]),
        "cantidad": cantidad,
        "iva": int(IVA * 100)
    }


@configurador.route("/confirmar", methods=["GET", "POST"])
def confirmar():

    if not es_cliente():
        return redirect(
            url_for(
                "auth.login",
                next=url_for("configurador.inicio")
            )
        )

    diseno = session.get("diseno_pendiente")

    # Revalidar por seguridad (la sesión podría traer datos viejos).
    if diseno:
        diseno, error = validar_diseno(diseno)

        if error:
            diseno = None

    if not diseno:

        flash(
            "Primero crea tu diseño y pulsa «Comprar este diseño».",
            "error"
        )

        return redirect(url_for("configurador.inicio"))

    cliente = obtener_cliente_actual()

    if request.method == "GET":

        return render_template(
            "configurador_confirmar.html",
            cliente=cliente,
            **datos_para_confirmar(diseno)
        )

    # ------------------------------------------------------
    # POST: crear el pedido
    # ------------------------------------------------------

    try:
        cantidad = int(request.form.get("cantidad", "1"))

        if cantidad < 1 or cantidad > 100:
            raise ValueError

    except (ValueError, TypeError):

        flash("Selecciona una cantidad válida entre 1 y 100.", "error")

        return render_template(
            "configurador_confirmar.html",
            cliente=cliente,
            **datos_para_confirmar(diseno)
        )

    documento = (request.form.get("documento") or "").strip()
    telefono = (request.form.get("telefono") or "").strip()
    direccion = (request.form.get("direccion") or "").strip()

    email = (session.get("usuario_email") or "").strip().lower()
    nombre = (session.get("usuario_nombre") or "").strip()

    if not email or not nombre:

        flash(
            "No se pudieron verificar tus datos. Inicia sesión nuevamente.",
            "error"
        )

        return redirect(url_for("auth.login"))

    # ----- cliente: crear o actualizar -----

    if cliente is None:

        if not documento:

            flash(
                "Debes ingresar tu documento para registrar la compra.",
                "error"
            )

            return render_template(
                "configurador_confirmar.html",
                cliente=None,
                **datos_para_confirmar(diseno, cantidad)
            )

        if Cliente.query.filter_by(documento=documento).first():

            flash(
                "El documento ingresado ya está asociado a otro "
                "registro de cliente. Verifica tus datos.",
                "error"
            )

            return render_template(
                "configurador_confirmar.html",
                cliente=None,
                **datos_para_confirmar(diseno, cantidad)
            )

        cliente = Cliente(
            nombre=nombre,
            documento=documento,
            telefono=telefono or None,
            email=email,
            direccion=direccion or None
        )

        db.session.add(cliente)

    else:

        if telefono:
            cliente.telefono = telefono

        if direccion:
            cliente.direccion = direccion

    # ----- pedido + factura en una sola transacción -----

    try:

        db.session.flush()

        pedido, factura = crear_pedido_desde_diseno(
            cliente,
            diseno,
            cantidad
        )

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print("ERROR AL REGISTRAR EL PEDIDO DEL DISEÑO:", error)

        flash(
            "No se pudo registrar tu pedido. "
            "Verifica los datos e inténtalo nuevamente.",
            "error"
        )

        return render_template(
            "configurador_confirmar.html",
            cliente=obtener_cliente_actual(),
            **datos_para_confirmar(diseno, cantidad)
        )

    session.pop("diseno_pendiente", None)

    flash(
        f"Pedido #{pedido.id} registrado. "
        f"Ahora realiza el pago para recibir tu factura.",
        "success"
    )

    return redirect(
        url_for("pagos.pagar", pedido_id=pedido.id)
    )


# =========================================================
# COMPATIBILIDAD CON cliente.html
# =========================================================

@configurador.route("/mostrar")
def mostrar_configurador():

    return redirect(
        url_for("configurador.inicio")
    )
