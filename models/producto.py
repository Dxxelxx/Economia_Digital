from database.connection import db


class Producto(db.Model):

    __tablename__ = "productos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    descripcion = db.Column(
        db.Text
    )

    precio_base = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    activo = db.Column(
        db.Boolean,
        default=True
    )

    # Relación con configuraciones
    configuraciones = db.relationship(
        "Configuracion",
        backref="producto",
        lazy=True
    )

    def __repr__(self):

        return f"<Producto {self.nombre}>"