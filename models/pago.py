from datetime import datetime

from database.connection import db


class Pago(db.Model):
    """
    Pago de un pedido realizado con criptomoneda (ETH) mediante MetaMask.

    Un pedido puede tener varios intentos de pago (por ejemplo, una
    transacción fallida y otra exitosa), pero cada transacción
    (tx_hash) solo puede registrarse una vez en todo el sistema.
    """

    __tablename__ = "pagos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedidos.id"),
        nullable=False,
        index=True
    )

    metodo = db.Column(
        db.String(50),
        nullable=False,
        default="ETH - MetaMask"
    )

    # Identificador de la red (11155111 = Sepolia, red de pruebas).
    chain_id = db.Column(
        db.Integer,
        nullable=False
    )

    # Billetera desde la que paga el cliente.
    wallet_cliente = db.Column(
        db.String(42)
    )

    # Billetera del taller que recibe el pago.
    wallet_destino = db.Column(
        db.String(42),
        nullable=False
    )

    # Hash de la transacción en la blockchain (único).
    tx_hash = db.Column(
        db.String(66),
        unique=True,
        nullable=False
    )

    # Valor del pedido en pesos colombianos al momento del pago.
    monto_cop = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    # Cuántos COP vale 1 ETH según la configuración (.env).
    tasa_eth_cop = db.Column(
        db.Numeric(18, 2),
        nullable=False
    )

    # Monto exigido en wei (1 ETH = 10^18 wei), guardado como texto
    # para no perder precisión.
    monto_wei = db.Column(
        db.String(40),
        nullable=False
    )

    # Monto en ETH, solo para mostrar.
    monto_eth = db.Column(
        db.Numeric(20, 8),
        nullable=False
    )

    # PENDIENTE, CONFIRMADO o FALLIDO.
    estado = db.Column(
        db.String(20),
        nullable=False,
        default="PENDIENTE"
    )

    confirmaciones = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    bloque = db.Column(
        db.Integer
    )

    detalle = db.Column(
        db.String(255)
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    fecha_confirmacion = db.Column(
        db.DateTime
    )

    pedido = db.relationship(
        "Pedido",
        backref=db.backref("pagos", lazy="dynamic")
    )

    def __repr__(self):
        return f"<Pago {self.tx_hash} {self.estado}>"
