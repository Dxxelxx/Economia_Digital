from database.connection import db
from datetime import datetime


class Configuracion(db.Model):

    __tablename__ = "configuraciones"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    producto_id = db.Column(
        db.Integer,
        db.ForeignKey("productos.id"),
        nullable=False
    )

    color = db.Column(
        db.String(50)
    )

    material = db.Column(
        db.String(100)
    )

    suela = db.Column(
        db.String(100)
    )

    herrajes = db.Column(
        db.String(100)
    )

    iniciales = db.Column(
        db.String(10)
    )

    precio = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    dias_entrega = db.Column(
        db.Integer,
        default=5
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Relación con pedidos
    pedidos = db.relationship(
        "Pedido",
        backref="configuracion",
        lazy=True
    )

    def __repr__(self):

        return f"<Configuracion {self.id}>"