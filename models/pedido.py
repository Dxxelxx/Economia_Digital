from database.connection import db
from datetime import datetime


class Pedido(db.Model):

    __tablename__ = "pedidos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=False
    )

    configuracion_id = db.Column(
        db.Integer,
        db.ForeignKey("configuraciones.id"),
        nullable=False
    )

    cantidad = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    subtotal = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    iva = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    total = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    estado = db.Column(
        db.String(50),
        nullable=False,
        default="Pendiente"
    )

    fecha_pedido = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    fecha_entrega = db.Column(
        db.Date
    )

    # Relación con producción
    produccion = db.relationship(
        "Produccion",
        backref="pedido",
        uselist=False
    )

    # Relación con factura
    factura = db.relationship(
        "Factura",
        backref="pedido",
        uselist=False
    )

    def __repr__(self):

        return f"<Pedido {self.id}>"