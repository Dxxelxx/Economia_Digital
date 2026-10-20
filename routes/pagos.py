from datetime import datetime
from decimal import Decimal

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    abort,
    current_app
)

from sqlalchemy.exc import IntegrityError

from database.connection import db

from models.cliente import Cliente
from models.pedido import Pedido
from models.pago import Pago

from servicies.pago_cripto_service import (
    PATRON_TX_HASH,
    PATRON_DIRECCION,
    ErrorRPC,
    calcular_monto_wei,
    wei_a_eth,
    crear_cliente_rpc,
    verificar_transaccion
)


pagos = Blueprint("pagos", __name__)


# ==========================================================
# AYUDAS
# ==========================================================

def pago_habilitado():
    """
    Los pagos con criptomoneda solo funcionan si el .env está
    completo y la billetera del taller tiene un formato válido.
    """

    config = current_app.config

    return bool(
        config.get("CRYPTO_PAYMENTS_ENABLED")
        and config.get("CRYPTO_RPC_URL")
        and PATRON_DIRECCION.match(
            config.get("TALLER_WALLET_ADDRESS") or ""
        )
        and Decimal(str(config.get("ETH_COP_RATE") or "0")) > 0
    )


def pedido_del_cliente(pedido_id):
    """
    Devuelve el pedido solo si pertenece al cliente que tiene la
    sesión iniciada. Si no, devuelve None.
    """

    if "usuario_id" not in session:
        return None

    if session.get("rol") != "cliente":
        return None

    email = (session.get("usuario_email") or "").strip().lower()

    if not email:
        return None

    cliente = Cliente.query.filter(
        db.func.lower(Cliente.email) == email
    ).first()

    if cliente is None:
        return None

    return Pedido.query.filter_by(
        id=pedido_id,
        cliente_id=cliente.id
    ).first()


def pago_confirmado(pedido):
    return pedido.pagos.filter_by(estado="CONFIRMADO").first()


def respuesta_json(datos, codigo=200):
    respuesta = jsonify(datos)
    respuesta.status_code = codigo
    return respuesta


def requiere_login_cliente(pedido_id):
    """Redirección para páginas HTML cuando no hay sesión de cliente."""

    if "usuario_id" not in session:
        return redirect(
            url_for(
                "auth.login",
                next=url_for("pagos.pagar", pedido_id=pedido_id)
            )
        )

    flash(
        "Solo los clientes pueden pagar pedidos.",
        "error"
    )

    return redirect(url_for("principal.inicio"))


# ==========================================================
# PÁGINA DE PAGO
# ==========================================================

@pagos.route("/<int:pedido_id>")
def pagar(pedido_id):

    pedido = pedido_del_cliente(pedido_id)

    if pedido is None:

        if "usuario_id" not in session or session.get("rol") != "cliente":
            return requiere_login_cliente(pedido_id)

        abort(404)

    # Si ya está pagado, mostrar el comprobante.
    if pago_confirmado(pedido):
        return redirect(
            url_for("pagos.pago_exitoso", pedido_id=pedido.id)
        )

    if pedido.estado == "Cancelado":

        flash(
            "Este pedido está cancelado y no se puede pagar.",
            "error"
        )

        return redirect(url_for("cliente.mis_pedidos"))

    if not pago_habilitado():

        flash(
            "El pago con criptomoneda no está disponible en este "
            "momento. Contacta al taller.",
            "error"
        )

        return redirect(
            url_for("cliente.detalle_pedido", pedido_id=pedido.id)
        )

    config = current_app.config

    tasa = Decimal(str(config["ETH_COP_RATE"]))

    monto_wei = calcular_monto_wei(pedido.total, tasa)

    # Si el cliente ya envió una transacción que aún no se
    # confirma, la página retoma su verificación.
    pago_pendiente = (
        pedido.pagos
        .filter_by(estado="PENDIENTE")
        .order_by(Pago.id.desc())
        .first()
    )

    return render_template(
        "pagar.html",
        pedido=pedido,
        monto_wei=str(monto_wei),
        monto_eth=wei_a_eth(monto_wei),
        tasa=tasa,
        wallet_destino=config["TALLER_WALLET_ADDRESS"],
        chain_id=config["CRYPTO_CHAIN_ID"],
        chain_id_hex=hex(config["CRYPTO_CHAIN_ID"]),
        confirmaciones_requeridas=config[
            "CRYPTO_REQUIRED_CONFIRMATIONS"
        ],
        tx_pendiente=pago_pendiente.tx_hash if pago_pendiente else ""
    )


# ==========================================================
# REGISTRAR LA TRANSACCIÓN ENVIADA DESDE METAMASK
# ==========================================================

@pagos.route("/<int:pedido_id>/registrar", methods=["POST"])
def registrar(pedido_id):

    pedido = pedido_del_cliente(pedido_id)

    if pedido is None:
        return respuesta_json(
            {"ok": False, "mensaje": "Pedido no encontrado."},
            404
        )

    if not pago_habilitado():
        return respuesta_json(
            {"ok": False, "mensaje": "Pagos no disponibles."},
            503
        )

    if pago_confirmado(pedido):
        return respuesta_json(
            {"ok": False, "mensaje": "Este pedido ya fue pagado."},
            409
        )

    datos = request.get_json(silent=True) or {}

    tx_hash = str(datos.get("tx_hash") or "").strip().lower()
    wallet = str(datos.get("wallet") or "").strip().lower()

    if not PATRON_TX_HASH.match(tx_hash):
        return respuesta_json(
            {"ok": False, "mensaje": "Hash de transacción inválido."},
            400
        )

    if wallet and not PATRON_DIRECCION.match(wallet):
        return respuesta_json(
            {"ok": False, "mensaje": "Dirección de billetera inválida."},
            400
        )

    # Una misma transacción no puede usarse para dos pedidos.
    existente = Pago.query.filter_by(tx_hash=tx_hash).first()

    if existente:

        if existente.pedido_id != pedido.id:
            return respuesta_json(
                {
                    "ok": False,
                    "mensaje": "Esa transacción ya fue usada en otro pedido."
                },
                409
            )

        return respuesta_json({"ok": True, "pago_id": existente.id})

    config = current_app.config

    tasa = Decimal(str(config["ETH_COP_RATE"]))

    monto_wei = calcular_monto_wei(pedido.total, tasa)

    pago = Pago(
        pedido_id=pedido.id,
        chain_id=config["CRYPTO_CHAIN_ID"],
        wallet_cliente=wallet or None,
        wallet_destino=config["TALLER_WALLET_ADDRESS"],
        tx_hash=tx_hash,
        monto_cop=pedido.total,
        tasa_eth_cop=tasa,
        monto_wei=str(monto_wei),
        monto_eth=wei_a_eth(monto_wei),
        estado="PENDIENTE"
    )

    try:

        db.session.add(pago)
        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        return respuesta_json(
            {"ok": False, "mensaje": "La transacción ya estaba registrada."},
            409
        )

    return respuesta_json({"ok": True, "pago_id": pago.id})


# ==========================================================
# VERIFICAR LA TRANSACCIÓN EN LA BLOCKCHAIN
# ==========================================================

@pagos.route("/<int:pedido_id>/verificar", methods=["POST"])
def verificar(pedido_id):

    pedido = pedido_del_cliente(pedido_id)

    if pedido is None:
        return respuesta_json(
            {"ok": False, "mensaje": "Pedido no encontrado."},
            404
        )

    if not pago_habilitado():
        return respuesta_json(
            {"ok": False, "mensaje": "Pagos no disponibles."},
            503
        )

    datos = request.get_json(silent=True) or {}

    tx_hash = str(datos.get("tx_hash") or "").strip().lower()

    consulta = pedido.pagos

    if tx_hash:
        consulta = consulta.filter_by(tx_hash=tx_hash)

    pago = consulta.order_by(Pago.id.desc()).first()

    if pago is None:
        return respuesta_json(
            {"ok": False, "mensaje": "No hay un pago registrado."},
            404
        )

    url_exito = url_for("pagos.pago_exitoso", pedido_id=pedido.id)

    if pago.estado == "CONFIRMADO":
        return respuesta_json({
            "ok": True,
            "estado": "CONFIRMADO",
            "confirmaciones": pago.confirmaciones,
            "redirigir": url_exito
        })

    config = current_app.config

    rpc = crear_cliente_rpc(config["CRYPTO_RPC_URL"])

    try:

        resultado = verificar_transaccion(
            rpc=rpc,
            tx_hash=pago.tx_hash,
            wallet_destino=pago.wallet_destino,
            monto_wei=int(pago.monto_wei),
            chain_id=pago.chain_id,
            confirmaciones_requeridas=config[
                "CRYPTO_REQUIRED_CONFIRMATIONS"
            ]
        )

    except ErrorRPC as error:

        # Fallo temporal de la red: no se cambia el estado.
        return respuesta_json({
            "ok": True,
            "estado": "PENDIENTE",
            "confirmaciones": pago.confirmaciones,
            "mensaje": str(error)
        })

    pago.estado = resultado["estado"]
    pago.confirmaciones = resultado["confirmaciones"]
    pago.bloque = resultado["bloque"]
    pago.detalle = (resultado["detalle"] or "")[:255]

    if resultado["wallet_origen"] and not pago.wallet_cliente:
        pago.wallet_cliente = resultado["wallet_origen"].lower()

    if resultado["estado"] == "CONFIRMADO":
        pago.fecha_confirmacion = datetime.utcnow()

    db.session.commit()

    respuesta = {
        "ok": True,
        "estado": pago.estado,
        "confirmaciones": pago.confirmaciones,
        "requeridas": config["CRYPTO_REQUIRED_CONFIRMATIONS"],
        "mensaje": pago.detalle
    }

    if pago.estado == "CONFIRMADO":
        respuesta["redirigir"] = url_exito

    return respuesta_json(respuesta)


# ==========================================================
# PAGO EXITOSO Y FACTURA
# ==========================================================

@pagos.route("/<int:pedido_id>/exito")
def pago_exitoso(pedido_id):

    pedido = pedido_del_cliente(pedido_id)

    if pedido is None:

        if "usuario_id" not in session or session.get("rol") != "cliente":
            return requiere_login_cliente(pedido_id)

        abort(404)

    pago = pago_confirmado(pedido)

    if pago is None:
        return redirect(
            url_for("pagos.pagar", pedido_id=pedido.id)
        )

    return render_template(
        "pago_exitoso.html",
        pedido=pedido,
        pago=pago,
        factura=pedido.factura
    )
