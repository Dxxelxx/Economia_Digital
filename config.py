import os
from dotenv import load_dotenv

load_dotenv()


def _como_booleano(valor):
    return str(valor or "").strip().lower() in (
        "1", "true", "yes", "si", "sí"
    )


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "clave-desarrollo"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------------------------------
    # PAGOS CON CRIPTOMONEDA (METAMASK)
    # ------------------------------------------------------

    CRYPTO_PAYMENTS_ENABLED = _como_booleano(
        os.getenv("CRYPTO_PAYMENTS_ENABLED")
    )

    # 11155111 = Sepolia (red de pruebas).
    CRYPTO_CHAIN_ID = int(
        os.getenv("CRYPTO_CHAIN_ID", "11155111")
    )

    CRYPTO_RPC_URL = os.getenv(
        "CRYPTO_RPC_URL",
        ""
    )

    # Billetera del taller que recibe los pagos.
    TALLER_WALLET_ADDRESS = os.getenv(
        "TALLER_WALLET_ADDRESS",
        ""
    ).strip()

    # Cuántos pesos colombianos (COP) vale 1 ETH.
    ETH_COP_RATE = os.getenv(
        "ETH_COP_RATE",
        "0"
    )

    CRYPTO_REQUIRED_CONFIRMATIONS = int(
        os.getenv("CRYPTO_REQUIRED_CONFIRMATIONS", "2")
    )
