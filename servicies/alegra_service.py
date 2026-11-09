import base64
import json
import os
from datetime import date

import requests


class AlegraError(Exception):
    """Error legible para mostrar al administrador."""

    def __init__(self, mensaje, cuerpo=None, codigo=None, http=None):
        super().__init__(mensaje)
        self.http = http
        self.cuerpo = cuerpo if isinstance(cuerpo, dict) else {}
        self.codigo = codigo


# ----------------------------------------------------------
# CONFIGURACIÓN
# ----------------------------------------------------------

def _cfg():
    return {
        "email": os.getenv("ALEGRA_EMAIL", "").strip(),
        "token": os.getenv("ALEGRA_TOKEN", "").strip(),
        "base": os.getenv(
            "ALEGRA_BASE_URL", "https://api.alegra.com/api/v1"
        ).rstrip("/"),
        "plantilla": os.getenv("ALEGRA_NUMBER_TEMPLATE_ID", "").strip(),
        "iva": os.getenv("ALEGRA_IVA_TAX_ID", "").strip(),
        "tipo_doc": os.getenv("ALEGRA_TIPO_DOCUMENTO", "CC").strip() or "CC",
        "stamp": os.getenv("ALEGRA_STAMP", "1").strip().lower()
                 in ("1", "true", "si", "sí", "yes"),
    }


def configurado():
    c = _cfg()
    return bool(c["email"] and c["token"])


def _cabeceras(c):
    credencial = f'{c["email"]}:{c["token"]}'.encode("utf-8")
    return {
        "Authorization": "Basic " + base64.b64encode(credencial).decode(),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def llamar(metodo, ruta, **kwargs):
    """Una llamada a la API de Alegra. Lanza AlegraError si falla."""

    c = _cfg()

    if not (c["email"] and c["token"]):
        raise AlegraError(
            "Faltan las credenciales de Alegra (ALEGRA_EMAIL y ALEGRA_TOKEN)."
        )

    try:
        r = requests.request(
            metodo,
            c["base"] + ruta,
            headers=_cabeceras(c),
            timeout=25,
            **kwargs
        )
    except requests.RequestException as error:
        raise AlegraError(f"No hay conexión con Alegra: {error}")

    if r.status_code == 401:
        raise AlegraError(
            "Alegra rechazó las credenciales (401). Revisa ALEGRA_EMAIL y ALEGRA_TOKEN."
        )

    if not r.ok:
        cuerpo = {}
        try:
            cuerpo = r.json()
            error = cuerpo.get("error") if isinstance(cuerpo.get("error"), dict) else {}
            detalle = (
                cuerpo.get("message")
                or error.get("message")
                or json.dumps(cuerpo, ensure_ascii=False)[:300]
            )
            codigo = error.get("code") or cuerpo.get("code")
        except Exception:
            detalle = (r.text or "")[:300]
            codigo = None
        raise AlegraError(
            f"Alegra respondió {r.status_code}: {detalle}",
            cuerpo=cuerpo,
            codigo=codigo,
            http=r.status_code,
        )

    if not r.content:
        return {}

    try:
        return r.json()
    except ValueError:
        raise AlegraError("Alegra devolvió una respuesta que no es JSON.")


# ----------------------------------------------------------
# CLIENTE Y PRODUCTO
# ----------------------------------------------------------

def _separar_nombre(nombre_completo):
    """
    'Daniel Becerra Solis' -> firstName=Daniel, lastName=Becerra, secondLastName=Solis
    1 palabra  -> nombre y apellido iguales (Alegra exige ambos)
    2 palabras -> nombre + apellido
    3 palabras -> nombre + 2 apellidos
    4 o más    -> 1.º y 2.º nombre + 2 apellidos
    """
    p = (nombre_completo or "").split()

    if not p:
        raise AlegraError("El cliente no tiene nombre.")

    if len(p) == 1:
        return {"firstName": p[0], "lastName": p[0]}

    if len(p) == 2:
        return {"firstName": p[0], "lastName": p[1]}

    if len(p) == 3:
        return {"firstName": p[0], "lastName": p[1], "secondLastName": p[2]}

    return {
        "firstName": p[0],
        "secondName": " ".join(p[1:-2]),
        "lastName": p[-2],
        "secondLastName": p[-1],
    }


def buscar_o_crear_contacto(cliente):

    c = _cfg()
    documento = (cliente.documento or "").strip()

    if not documento:
        raise AlegraError(
            "El cliente no tiene documento: la factura electrónica lo exige."
        )

    encontrados = llamar("GET", "/contacts", params={"identification": documento})

    if isinstance(encontrados, list) and encontrados:
        return encontrados[0]["id"]

    es_empresa = c["tipo_doc"].upper() == "NIT"

    nuevo = {
        "name": cliente.nombre,
        "identification": documento,
        "identificationObject": {"type": c["tipo_doc"], "number": documento},
        "kindOfPerson": "LEGAL_ENTITY" if es_empresa else "PERSON_ENTITY",
        "regime": "SIMPLIFIED_REGIME",
        "type": ["client"],
    }

    # Para personas, Alegra Colombia exige el nombre separado (nameObject).
    if not es_empresa:
        nuevo["nameObject"] = _separar_nombre(cliente.nombre)

    if cliente.email:
        nuevo["email"] = cliente.email

    if cliente.telefono:
        nuevo["phonePrimary"] = cliente.telefono

    if cliente.direccion:
        nuevo["address"] = {"address": cliente.direccion}

    return llamar("POST", "/contacts", json=nuevo)["id"]


def buscar_o_crear_item(nombre, precio_unitario):

    c = _cfg()

    encontrados = llamar("GET", "/items", params={"query": nombre})

    if isinstance(encontrados, list):
        for item in encontrados:
            if (item.get("name") or "").strip().lower() == nombre.strip().lower():
                return item["id"]

    nuevo = {"name": nombre, "price": float(precio_unitario)}

    if c["iva"]:
        nuevo["tax"] = [{"id": int(c["iva"])}]

    return llamar("POST", "/items", json=nuevo)["id"]


# ----------------------------------------------------------
# FACTURA
# ----------------------------------------------------------

def _leer_registro(factura):
    """Respuesta de Alegra guardada antes en factura.xml (si existe)."""
    try:
        datos = json.loads(factura.xml or "")
        return datos if isinstance(datos, dict) else {}
    except ValueError:
        return {}


def _interpretar(respuesta):
    stamp = respuesta.get("stamp") or {}
    plantilla = respuesta.get("numberTemplate") or {}

    cufe = stamp.get("cufe") or respuesta.get("cufe")
    legal = str(stamp.get("legalStatus") or "").upper()

    if cufe:
        estado = "ACEPTADA"
    elif "REJECT" in legal or "ERROR" in legal:
        estado = "RECHAZADA"
    else:
        estado = "PENDIENTE"

    return {
        "alegra_id": respuesta.get("id"),
        "cufe": cufe,
        "estado": estado,
        "legal": legal,
        "numero": plantilla.get("fullNumber"),
        "prefijo": plantilla.get("prefix"),
    }


def emitir_factura(factura):
    """Emite la factura en Alegra y actualiza el objeto Factura."""

    c = _cfg()

    if not c["plantilla"]:
        raise AlegraError(
            "Falta ALEGRA_NUMBER_TEMPLATE_ID (resolución de numeración). "
            "Ejecuta probar_alegra.py para ver los ids."
        )

    if not c["iva"]:
        raise AlegraError(
            "Falta ALEGRA_IVA_TAX_ID (id del IVA 19 %). "
            "Ejecuta probar_alegra.py para ver los ids."
        )

    if (factura.estado_dian or "").upper() == "ACEPTADA" and factura.cufe:
        return {"ya_emitida": True, "cufe": factura.cufe}

    # Evita duplicar: si ya se creó en Alegra pero no quedó timbrada.
    previo = _leer_registro(factura)
    if previo.get("id"):
        try:
            actual = llamar("GET", f'/invoices/{previo["id"]}')
        except AlegraError as error:
            if error.http != 404:
                raise
            actual = None   # la borraron en Alegra: se puede crear de nuevo

        if actual is not None:
            datos = _interpretar(actual)
            if datos["cufe"]:
                _guardar(factura, actual, datos)
                return datos
            raise AlegraError(
                f'La factura ya existe en Alegra (id {previo["id"]}) pero '
                "aún no está timbrada. Revísala o emítela desde Alegra para no duplicarla."
            )

    pedido = factura.pedido
    cliente = pedido.cliente
    producto = pedido.configuracion.producto
    cantidad = int(pedido.cantidad or 1)
    precio_unitario = float(pedido.subtotal) / cantidad

    contacto_id = buscar_o_crear_contacto(cliente)
    item_id = buscar_o_crear_item(producto.nombre, precio_unitario)

    hoy = date.today().isoformat()

    cuerpo = {
        "date": hoy,
        "dueDate": hoy,
        "client": {"id": contacto_id},
        "numberTemplate": {"id": int(c["plantilla"])},
        "paymentForm": "CASH",
        "paymentMethod": "CASH",
        "items": [{
            "id": item_id,
            "price": precio_unitario,
            "quantity": cantidad,
            "tax": [{"id": int(c["iva"])}],
        }],
        "observations": (
            f"Pedido #{pedido.id} - Taller El Obrero"
            + (f" - Talla {pedido.configuracion.talla}"
               if getattr(pedido.configuracion, "talla", None) else "")
        ),
    }

    if c["stamp"]:
        cuerpo["stamp"] = {"generateStamp": True}

    try:
        respuesta = llamar("POST", "/invoices", json=cuerpo)

    except AlegraError as error:
        # Alegra a veces CREA la factura y falla solo al enviarla a la DIAN
        # (p. ej. la compañía no está habilitada para facturar electrónicamente).
        # Se guarda lo creado para no duplicar y se devuelve un aviso.
        creada = error.cuerpo.get("invoice")

        if isinstance(creada, dict) and creada.get("id"):
            datos = _interpretar(creada)
            datos["estado"] = "PENDIENTE"
            _guardar(factura, creada, datos)
            datos["advertencia"] = (
                f'La factura quedó creada en Alegra (id {creada["id"]}) pero '
                f"no se pudo enviar a la DIAN: {error}"
            )
            return datos

        raise

    datos = _interpretar(respuesta)
    _guardar(factura, respuesta, datos)

    return datos


def _guardar(factura, respuesta, datos):

    factura.estado_dian = datos["estado"]

    if datos["cufe"]:
        factura.cufe = datos["cufe"]

    if datos["prefijo"]:
        factura.prefijo = str(datos["prefijo"])[:10]

    # Respuesta completa de Alegra, para auditoría y para no duplicar.
    factura.xml = json.dumps(respuesta, ensure_ascii=False)
