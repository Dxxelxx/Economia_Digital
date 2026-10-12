from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

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
from models.producto import Producto
from models.configuracion import Configuracion
from models.pedido import Pedido
from models.cliente import Cliente


pedidos = Blueprint("pedidos", __name__)


def obtener_cliente_actual():
    """
    Busca al cliente asociado con la sesión iniciada.
    """

    email = session.get("usuario_email")

    if not email:
        return None

    return Cliente.query.filter_by(
        email=email.lower()
    ).first()


@pedidos.route("/")
def mostrar_pedidos():

    if "usuario_id" not in session:
        return redirect(url_for("auth.login"))

    return redirect(url_for("cliente.mis_pedidos"))


@pedidos.route("/comprar/<int:producto_id>", methods=["GET", "POST"])
def comprar(producto_id):

    # --------------------------------------------------
    # 1. Verificar sesión
    # --------------------------------------------------

    if "usuario_id" not in session:
        return redirect(
            url_for(
                "auth.login",
                next=url_for(
                    "pedidos.comprar",
                    producto_id=producto_id
                )
            )
        )

    if session.get("rol") != "cliente":
        flash(
            "Solo los clientes pueden realizar compras.",
            "error"
        )
        return redirect(url_for("principal.inicio"))

    # --------------------------------------------------
    # 2. Buscar producto
    # --------------------------------------------------

    producto = Producto.query.get_or_404(producto_id)

    if not producto.activo:
        flash(
            "Este producto no está disponible actualmente.",
            "error"
        )
        return redirect(url_for("principal.inicio"))

    if request.method == "GET":
        return render_template(
            "confirmar_compra.html",
            producto=producto
        )

    # --------------------------------------------------
    # 3. Validar cantidad
    # --------------------------------------------------

    try:
        cantidad = int(request.form.get("cantidad", "1"))

        if cantidad < 1 or cantidad > 100:
            raise ValueError

    except (ValueError, TypeError):
        flash(
            "Selecciona una cantidad válida entre 1 y 100.",
            "error"
        )
        return render_template(
            "confirmar_compra.html",
            producto=producto
        )

    # --------------------------------------------------
    # 4. Obtener datos del cliente
    # --------------------------------------------------

    email = (
        session.get("usuario_email") or ""
    ).strip().lower()

    nombre = (
        session.get("usuario_nombre") or ""
    ).strip()

    if not email or not nombre:
        flash(
            "No se pudieron verificar tus datos de usuario. "
            "Inicia sesión nuevamente.",
            "error"
        )
        return redirect(url_for("auth.login"))

    cliente_actual = obtener_cliente_actual()

    documento = (
        request.form.get("documento") or ""
    ).strip()

    telefono = (
        request.form.get("telefono") or ""
    ).strip()

    direccion = (
        request.form.get("direccion") or ""
    ).strip()

    # --------------------------------------------------
    # 5. Crear o actualizar el registro del cliente
    # --------------------------------------------------

    if cliente_actual is None:

        if not documento:
            flash(
                "Debes ingresar tu documento para registrar la compra.",
                "error"
            )
            return render_template(
                "confirmar_compra.html",
                producto=producto
            )

        documento_existente = Cliente.query.filter_by(
            documento=documento
        ).first()

        if documento_existente:
            flash(
                "El documento ingresado ya está asociado "
                "a otro registro de cliente. Verifica tus datos.",
                "error"
            )
            return render_template(
                "confirmar_compra.html",
                producto=producto
            )

        cliente_actual = Cliente(
            nombre=nombre,
            documento=documento,
            telefono=telefono or None,
            email=email,
            direccion=direccion or None
        )

        db.session.add(cliente_actual)

    else:

        if telefono:
            cliente_actual.telefono = telefono

        if direccion:
            cliente_actual.direccion = direccion

        # El documento no se cambia automáticamente.
        # Si ya existe un cliente, se conserva su registro.

    # --------------------------------------------------
    # 6. Calcular los valores
    # --------------------------------------------------

    try:
        precio_unitario = Decimal(str(producto.precio_base))

        if precio_unitario <= 0:
            raise ValueError

    except (InvalidOperation, ValueError, TypeError):
        flash(
            "El precio de este producto no es válido. "
            "Contacta al administrador.",
            "error"
        )
        db.session.rollback()

        return redirect(
            url_for(
                "cliente.producto",
                producto_id=producto.id
            )
        )

    subtotal = (precio_unitario * cantidad).quantize(
        Decimal("0.01")
    )

    iva = (subtotal * Decimal("0.19")).quantize(
        Decimal("0.01")
    )

    total = subtotal + iva

    # --------------------------------------------------
    # 7. Crear configuración básica del producto
    # --------------------------------------------------
    # Pedido exige configuracion_id. Para una compra del
    # catálogo se registra una configuración estándar.
    # No se obliga al cliente a utilizar el configurador.

    configuracion = Configuracion(
        producto_id=producto.id,
        color="Estándar",
        material="Estándar",
        suela="Estándar",
        herrajes="Estándar",
        iniciales="",
        precio=precio_unitario,
        dias_entrega=5
    )

    try:
        db.session.add(configuracion)
        db.session.flush()

        # Obtener el ID del cliente creado o existente.
        db.session.flush()

        # --------------------------------------------------
        # 8. Crear el pedido
        # --------------------------------------------------

        fecha_entrega = (
            datetime.utcnow() + timedelta(days=5)
        ).date()

        nuevo_pedido = Pedido(
            cliente_id=cliente_actual.id,
            configuracion_id=configuracion.id,
            cantidad=cantidad,
            subtotal=subtotal,
            iva=iva,
            total=total,
            estado="Pendiente",
            fecha_entrega=fecha_entrega
        )

        db.session.add(nuevo_pedido)
        db.session.commit()

        flash(
            f"¡Compra registrada! Tu pedido es el "
            f"#{nuevo_pedido.id}.",
            "success"
        )

        return redirect(
            url_for(
                "cliente.detalle_pedido",
                pedido_id=nuevo_pedido.id
            )
        )

    except Exception as error:
        db.session.rollback()

        print("ERROR AL REGISTRAR LA COMPRA:", error)

        flash(
            "No se pudo registrar la compra. "
            "Verifica tus datos e inténtalo nuevamente.",
            "error"
        )

        return render_template(
            "confirmar_compra.html",
            producto=producto
        )