from database.connection import db
from datetime import datetime


class Produccion(db.Model):

    __tablename__ = "produccion"

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

    estado = db.Column(
        db.String(50),
        nullable=False,
        default="Pendiente"
    )

    fecha_inicio = db.Column(
        db.DateTime
    )

    fecha_finalizacion = db.Column(
        db.DateTime
    )

    observaciones = db.Column(
        db.Text
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):

        return f"<Produccion Pedido {self.pedido_id}>"