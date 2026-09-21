from database.connection import db
from datetime import datetime


class Factura(db.Model):

    __tablename__ = "facturas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedidos.id"),
        nullable=False,
        unique=True
    )

    numero = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    prefijo = db.Column(
        db.String(10)
    )

    fecha = db.Column(
        db.DateTime,
        default=datetime.utcnow
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

    estado_dian = db.Column(
        db.String(50),
        default="PENDIENTE"
    )

    cufe = db.Column(
        db.String(200)
    )

    xml = db.Column(
        db.Text
    )

    qr = db.Column(
        db.Text
    )

    pdf = db.Column(
        db.String(255)
    )

    def __repr__(self):

        return f"<Factura {self.numero}>"