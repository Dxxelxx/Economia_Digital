from database.connection import db
from datetime import datetime


class Inventario(db.Model):

    __tablename__ = "inventario"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    material = db.Column(
        db.String(100),
        nullable=False
    )

    descripcion = db.Column(
        db.Text
    )

    cantidad = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    unidad = db.Column(
        db.String(30),
        nullable=False,
        default="unidad"
    )

    minimo = db.Column(
        db.Numeric(10, 2),
        default=0
    )

    fecha_actualizacion = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):

        return f"<Inventario {self.material}>"