"""
Creación de un pedido y su factura a partir de un diseño del
configurador. Hace lo mismo que la compra desde el catálogo
(routes/pedidos.py): subtotal, IVA 19 %, pedido "Pendiente" y
factura "PENDIENTE", todo en una sola transacción.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from database.connection import db

from models.configuracion import Configuracion
from models.factura import Factura
from models.pedido import Pedido
from models.producto import Producto

from servicies.calculadora_entrega import calcular_entrega
from servicies.configurador_service import (
    PRODUCTOS,
    describir_diseno
)


def obtener_producto_personalizado(clave):
    """
    Producto que agrupa los diseños personalizados de una categoría
    (por ejemplo "Zapato artesanal personalizado"). Se crea la primera
    vez y queda inactivo para que no aparezca en el catálogo de venta.
    """

    definicion = PRODUCTOS[clave]
    nombre = f"{definicion['nombre']} personalizado"

    producto = Producto.query.filter_by(nombre=nombre).first()

    if producto is None:

        producto = Producto(
            nombre=nombre,
            descripcion="Diseño creado por el cliente en el configurador 3D.",
            categoria=definicion["categoria"],
            precio_base=definicion["base"],
            activo=False
        )

        db.session.add(producto)
        db.session.flush()

    return producto


def crear_pedido_desde_diseno(cliente, diseno, cantidad):
    """
    Agrega a la sesión (sin confirmar) la configuración, el pedido y la
    factura. Quien llama debe hacer commit o rollback.

    Devuelve (pedido, factura).
    """

    textos = describir_diseno(diseno)
    dias = calcular_entrega(cantidad)

    precio_unitario = Decimal(str(diseno["precio_unitario"]))

    subtotal = (precio_unitario * cantidad).quantize(Decimal("0.01"))
    iva = (subtotal * Decimal("0.19")).quantize(Decimal("0.01"))
    total = (subtotal + iva).quantize(Decimal("0.01"))

    producto = obtener_producto_personalizado(diseno["producto"])

    configuracion = Configuracion(
        producto_id=producto.id,
        color=textos["color"],
        material=textos["material"],
        suela=textos["suela"],
        herrajes=textos["herrajes"],
        iniciales=textos["iniciales"],
        precio=precio_unitario,
        dias_entrega=dias
    )

    db.session.add(configuracion)
    db.session.flush()

    pedido = Pedido(
        cliente_id=cliente.id,
        configuracion_id=configuracion.id,
        cantidad=cantidad,
        subtotal=subtotal,
        iva=iva,
        total=total,
        estado="Pendiente",
        fecha_entrega=(datetime.utcnow() + timedelta(days=dias)).date()
    )

    db.session.add(pedido)
    db.session.flush()

    factura = Factura(
        pedido_id=pedido.id,
        numero=f"FE-{pedido.id:06d}",
        prefijo="FE",
        fecha=datetime.utcnow(),
        subtotal=subtotal,
        iva=iva,
        total=total,
        estado_dian="PENDIENTE"
    )

    db.session.add(factura)

    return pedido, factura
