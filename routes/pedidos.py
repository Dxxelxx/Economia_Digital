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
from models.factura import Factura


pedidos = Blueprint("pedidos", __name__)


# ==========================================================
# OBTENER CLIENTE ACTUAL
# ==========================================================

def obtener_cliente_actual():
    """
    Busca el registro de cliente asociado al correo
    electrónico almacenado en la sesión.
    """

    email = (
        session.get("usuario_email") or ""
    ).strip().lower()

    if not email:
        return None

    return Cliente.query.filter(
        db.func.lower(Cliente.email) == email
    ).first()


# ==========================================================
# LISTADO DE PEDIDOS
# ==========================================================

@pedidos.route("/")
def mostrar_pedidos():

    if "usuario_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    if session.get("rol") != "cliente":
        flash(
            "No tienes permisos para acceder a los pedidos de clientes.",
            "error"
        )
        return redirect(
            url_for("principal.inicio")
        )

    return redirect(
        url_for("cliente.mis_pedidos")
    )


# ==========================================================
# COMPRAR PRODUCTO
# ==========================================================

@pedidos.route(
    "/comprar/<int:producto_id>",
    methods=["GET", "POST"]
)
def comprar(producto_id):

    # ------------------------------------------------------
    # 1. VERIFICAR SESIÓN
    # ------------------------------------------------------

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

        return redirect(
            url_for("principal.inicio")
        )

    # ------------------------------------------------------
    # 2. BUSCAR PRODUCTO
    # ------------------------------------------------------

    producto = Producto.query.get_or_404(producto_id)

    if not producto.activo:
        flash(
            "Este producto no está disponible actualmente.",
            "error"
        )

        return redirect(
            url_for("principal.inicio")
        )

    # Mostrar formulario de compra.
    if request.method == "GET":
        return render_template(
            "confirmar_compra.html",
            producto=producto
        )

    # ------------------------------------------------------
    # 3. VALIDAR CANTIDAD
    # ------------------------------------------------------

    try:
        cantidad = int(
            request.form.get("cantidad", "1")
        )

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

    # ------------------------------------------------------
    # 4. OBTENER DATOS DEL CLIENTE
    # ------------------------------------------------------

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

        return redirect(
            url_for("auth.login")
        )

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

    # ------------------------------------------------------
    # 5. CREAR O ACTUALIZAR CLIENTE
    # ------------------------------------------------------

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

        # Se conserva el documento que ya existe.

    # ------------------------------------------------------
    # 6. CALCULAR SUBTOTAL, IVA Y TOTAL
    # ------------------------------------------------------

    try:
        precio_unitario = Decimal(
            str(producto.precio_base)
        )

        if precio_unitario <= 0:
            raise ValueError

    except (InvalidOperation, ValueError, TypeError):

        db.session.rollback()

        flash(
            "El precio de este producto no es válido. "
            "Contacta al administrador.",
            "error"
        )

        return redirect(
            url_for(
                "cliente.producto",
                producto_id=producto.id
            )
        )

    subtotal = (
        precio_unitario * cantidad
    ).quantize(
        Decimal("0.01")
    )

    iva = (
        subtotal * Decimal("0.19")
    ).quantize(
        Decimal("0.01")
    )

    total = (
        subtotal + iva
    ).quantize(
        Decimal("0.01")
    )

    # ------------------------------------------------------
    # 7. CREAR CONFIGURACIÓN ESTÁNDAR
    # ------------------------------------------------------
    # El modelo Pedido exige configuracion_id.
    # Por eso se crea una configuración básica para
    # las compras realizadas desde el catálogo.

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

    # ------------------------------------------------------
    # 8. CREAR PEDIDO Y FACTURA EN UNA TRANSACCIÓN
    # ------------------------------------------------------

    try:

        # Guardar el cliente si es nuevo y obtener su ID.
        db.session.flush()

        # Crear la configuración.
        db.session.add(configuracion)
        db.session.flush()

        # Calcular fecha de entrega.
        fecha_entrega = (
            datetime.utcnow() + timedelta(days=5)
        ).date()

        # Crear el pedido.
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

        # Obtener el ID del pedido sin confirmar
        # todavía la transacción.
        db.session.flush()

        # --------------------------------------------------
        # 9. GENERAR NÚMERO Y CREAR FACTURA
        # --------------------------------------------------

        numero_factura = (
            f"FE-{nuevo_pedido.id:06d}"
        )

        nueva_factura = Factura(
            pedido_id=nuevo_pedido.id,
            numero=numero_factura,
            prefijo="FE",
            fecha=datetime.utcnow(),
            subtotal=subtotal,
            iva=iva,
            total=total,
            estado_dian="PENDIENTE"
        )

        db.session.add(nueva_factura)

        # --------------------------------------------------
        # 10. GUARDAR TODA LA OPERACIÓN
        # --------------------------------------------------
        # Si algo falla antes de este commit, el except
        # ejecutará rollback y evitará guardar una compra
        # incompleta.

        db.session.commit()

        # --------------------------------------------------
        # 11. CONFIRMAR COMPRA
        # --------------------------------------------------

        flash(
            f"¡Compra registrada! Tu pedido es el "
            f"#{nuevo_pedido.id} y tu factura es "
            f"{numero_factura}.",
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

        print(
            "ERROR AL REGISTRAR PEDIDO Y FACTURA:",
            error
        )

        flash(
            "No se pudo registrar la compra y generar "
            "su factura. Verifica los datos e inténtalo nuevamente.",
            "error"
        )

        return render_template(
            "confirmar_compra.html",
            producto=producto
        )