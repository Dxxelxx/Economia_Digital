from database.connection import db


class Producto(db.Model):

    __tablename__ = "productos"


    # =========================================
    # ID
    # =========================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )


    # =========================================
    # INFORMACIÓN
    # =========================================

    nombre = db.Column(
        db.String(100),
        nullable=False
    )


    descripcion = db.Column(
        db.Text,
        nullable=True
    )


    categoria = db.Column(
        db.String(50),
        nullable=False,
        default="Accesorios"
    )


    imagen = db.Column(
        db.String(255),
        nullable=True
    )


    # =========================================
    # PRECIO
    # =========================================

    precio_base = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )


    # =========================================
    # ESTADO
    # =========================================

    activo = db.Column(
        db.Boolean,
        default=True
    )


    # =========================================
    # RELACIÓN CONFIGURACIONES
    # =========================================

    configuraciones = db.relationship(
        "Configuracion",
        backref="producto",
        lazy=True
    )


    # =========================================
    # PROPIEDAD PRECIO
    # =========================================

    @property
    def precio(self):

        return self.precio_base


    # =========================================
    # REPRESENTACIÓN
    # =========================================

    def __repr__(self):

        return f"<Producto {self.nombre}>"