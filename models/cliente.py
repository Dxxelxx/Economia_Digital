from database.connection import db
from datetime import datetime


class Cliente(db.Model):

    __tablename__ = "clientes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    documento = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    telefono = db.Column(
        db.String(30)
    )

    email = db.Column(
        db.String(120)
    )

    direccion = db.Column(
        db.String(200)
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Relación con pedidos
    pedidos = db.relationship(
        "Pedido",
        backref="cliente",
        lazy=True
    )

    def __repr__(self):

        return f"<Cliente {self.nombre}>"