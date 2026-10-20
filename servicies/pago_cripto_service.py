"""
Lógica de pagos en ETH.

Este módulo no depende de Flask ni de la base de datos, para que
pueda probarse por separado. La verificación se hace SIEMPRE en el
servidor, consultando la blockchain: nunca se confía en lo que
diga el navegador del cliente.
"""

import re
from decimal import Decimal, ROUND_UP, localcontext

import requests


WEI_POR_ETH = Decimal(10) ** 18

PATRON_TX_HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")
PATRON_DIRECCION = re.compile(r"^0x[0-9a-fA-F]{40}$")


class ErrorRPC(Exception):
    """No se pudo consultar el nodo de la blockchain."""


# ==========================================================
# CONVERSIONES
# ==========================================================

def calcular_monto_wei(total_cop, tasa_eth_cop):
    """
    Convierte un total en pesos colombianos al monto exacto en wei
    que el cliente debe pagar. Se redondea hacia arriba para que
    nunca quede por debajo del valor del pedido.
    """

    total = Decimal(str(total_cop))
    tasa = Decimal(str(tasa_eth_cop))

    if total <= 0 or tasa <= 0:
        raise ValueError("Total y tasa deben ser mayores que cero.")

    with localcontext() as contexto:
        contexto.prec = 60
        wei = (total / tasa * WEI_POR_ETH).quantize(
            Decimal(1),
            rounding=ROUND_UP
        )

    return int(wei)


def wei_a_eth(wei):
    """Convierte wei a ETH con 8 decimales (solo para mostrar)."""

    with localcontext() as contexto:
        contexto.prec = 60
        return (Decimal(int(wei)) / WEI_POR_ETH).quantize(
            Decimal("0.00000001"),
            rounding=ROUND_UP
        )


# ==========================================================
# CONSULTA A LA BLOCKCHAIN (JSON-RPC)
# ==========================================================

def crear_cliente_rpc(url, tiempo_espera=15):
    """
    Devuelve una función rpc(metodo, parametros) que consulta
    el nodo indicado.
    """

    def rpc(metodo, parametros=None):

        try:
            respuesta = requests.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": metodo,
                    "params": parametros or []
                },
                timeout=tiempo_espera
            )

            respuesta.raise_for_status()

            datos = respuesta.json()

        except (requests.RequestException, ValueError) as error:
            raise ErrorRPC(
                f"No se pudo consultar la red: {error}"
            ) from error

        if "error" in datos and datos["error"]:
            mensaje = datos["error"].get("message", "error desconocido")
            raise ErrorRPC(f"El nodo respondió con un error: {mensaje}")

        return datos.get("result")

    return rpc


def _a_entero(valor):
    """Convierte un número hexadecimal ('0x1a') a entero."""
    return int(valor, 16)


# ==========================================================
# VERIFICACIÓN DE UNA TRANSACCIÓN
# ==========================================================

def verificar_transaccion(
    rpc,
    tx_hash,
    wallet_destino,
    monto_wei,
    chain_id,
    confirmaciones_requeridas
):
    """
    Comprueba en la blockchain que la transacción:

      1. está en la red correcta;
      2. existe y fue enviada a la billetera del taller;
      3. transfiere al menos el monto exigido;
      4. se ejecutó con éxito;
      5. ya tiene las confirmaciones necesarias.

    Devuelve un diccionario con:
      estado: CONFIRMADO, PENDIENTE o FALLIDO
      confirmaciones, bloque, wallet_origen, detalle
    """

    resultado = {
        "estado": "PENDIENTE",
        "confirmaciones": 0,
        "bloque": None,
        "wallet_origen": None,
        "detalle": ""
    }

    # 1. Red correcta.
    red_actual = _a_entero(rpc("eth_chainId"))

    if red_actual != int(chain_id):
        resultado["estado"] = "FALLIDO"
        resultado["detalle"] = (
            f"El nodo está en otra red ({red_actual}); "
            f"se esperaba la red {chain_id}."
        )
        return resultado

    # 2. La transacción existe.
    transaccion = rpc("eth_getTransactionByHash", [tx_hash])

    if not transaccion:
        resultado["detalle"] = (
            "La transacción todavía no aparece en la red."
        )
        return resultado

    resultado["wallet_origen"] = transaccion.get("from")

    # 3. Destino y monto correctos.
    destino = (transaccion.get("to") or "").lower()

    if destino != wallet_destino.lower():
        resultado["estado"] = "FALLIDO"
        resultado["detalle"] = (
            "La transacción no fue enviada a la billetera del taller."
        )
        return resultado

    valor_enviado = _a_entero(transaccion.get("value", "0x0"))

    if valor_enviado < int(monto_wei):
        resultado["estado"] = "FALLIDO"
        resultado["detalle"] = (
            "El monto enviado es menor al valor del pedido."
        )
        return resultado

    # 4. Resultado de la ejecución.
    recibo = rpc("eth_getTransactionReceipt", [tx_hash])

    if not recibo or not recibo.get("blockNumber"):
        resultado["detalle"] = (
            "Transacción enviada; esperando que entre en un bloque."
        )
        return resultado

    if _a_entero(recibo.get("status", "0x0")) != 1:
        resultado["estado"] = "FALLIDO"
        resultado["detalle"] = "La transacción fue revertida por la red."
        return resultado

    # 5. Confirmaciones.
    bloque = _a_entero(recibo["blockNumber"])
    ultimo_bloque = _a_entero(rpc("eth_blockNumber"))

    confirmaciones = max(ultimo_bloque - bloque + 1, 0)

    resultado["bloque"] = bloque
    resultado["confirmaciones"] = confirmaciones

    if confirmaciones >= int(confirmaciones_requeridas):
        resultado["estado"] = "CONFIRMADO"
        resultado["detalle"] = "Pago confirmado en la blockchain."
    else:
        resultado["detalle"] = (
            f"Esperando confirmaciones: {confirmaciones} de "
            f"{confirmaciones_requeridas}."
        )

    return resultado
