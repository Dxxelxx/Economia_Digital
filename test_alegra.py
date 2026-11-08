import json, os, sys, types
sys.path.insert(0, ".")
os.environ.update(ALEGRA_EMAIL="a@b.co", ALEGRA_TOKEN="tok", ALEGRA_NUMBER_TEMPLATE_ID="7", ALEGRA_IVA_TAX_ID="3")
import servicies.alegra_service as s

llamadas = []
def respuesta(codigo, cuerpo):
    r = types.SimpleNamespace(status_code=codigo, ok=codigo < 400, content=b"x", text=json.dumps(cuerpo))
    r.json = lambda: cuerpo
    return r

estado = {"contactos": [], "stamp": True}
def falso(metodo, url, headers=None, timeout=None, **kw):
    ruta = url.split("/api/v1")[1]
    llamadas.append((metodo, ruta, kw))
    assert headers["Authorization"].startswith("Basic ")
    if (metodo, ruta) == ("GET", "/contacts"): return respuesta(200, estado["contactos"])
    if (metodo, ruta) == ("POST", "/contacts"):
        estado["contactos"] = [{"id": 11}]; return respuesta(201, {"id": 11})
    if (metodo, ruta) == ("GET", "/items"): return respuesta(200, [])
    if (metodo, ruta) == ("POST", "/items"): return respuesta(201, {"id": 22})
    if (metodo, ruta) == ("POST", "/invoices"):
        out = {"id": 99, "numberTemplate": {"fullNumber": "FE1", "prefix": "FE"}}
        if estado["stamp"]: out["stamp"] = {"cufe": "CUFE-ABC", "legalStatus": "STAMPED"}
        return respuesta(201, out)
    if metodo == "GET" and ruta == "/invoices/99":
        return respuesta(200, {"id": 99, "stamp": {"cufe": "CUFE-ABC"}} if estado.get("listo") else {"id": 99})
    return respuesta(404, {"message": "no existe"})
s.requests.request = falso

N = types.SimpleNamespace
def nueva():
    ped = N(id=5, cantidad=2, subtotal=640000, cliente=N(nombre="Fabian", documento="123", email="f@x.co", telefono="3", direccion="Cll"),
            configuracion=N(producto=N(nombre="Zapato personalizado")))
    f = N(estado_dian="PENDIENTE", cufe=None, xml=None, prefijo=None, pedido=ped); return f

f = nueva(); d = s.emitir_factura(f)
assert f.estado_dian == "ACEPTADA" and f.cufe == "CUFE-ABC" and f.prefijo == "FE", f.__dict__
inv = [c for c in llamadas if c[1] == "/invoices"][0][2]["json"]
assert inv["items"][0]["price"] == 320000 and inv["items"][0]["quantity"] == 2
assert inv["stamp"] == {"generateStamp": True} and inv["numberTemplate"] == {"id": 7} and inv["client"] == {"id": 11}
assert s.emitir_factura(f)["ya_emitida"]  # no duplica
# sin CUFE: queda pendiente y reintento no duplica
estado["stamp"] = False; g = nueva(); s.emitir_factura(g)
assert g.estado_dian == "PENDIENTE" and json.loads(g.xml)["id"] == 99
n = len([c for c in llamadas if c == c and c[0] == "POST" and c[1] == "/invoices"])
try: s.emitir_factura(g); raise SystemExit("debía avisar")
except s.AlegraError as e: assert "no está timbrada" in str(e)
estado["listo"] = True; r = s.emitir_factura(g)   # ahora Alegra ya la timbró: se sincroniza
assert g.estado_dian == "ACEPTADA" and g.cufe == "CUFE-ABC"
assert len([c for c in llamadas if c[0] == "POST" and c[1] == "/invoices"]) == n  # sin segundo POST
# cliente sin documento / sin credenciales / 401
h = nueva(); h.pedido.cliente.documento = ""
try: s.emitir_factura(h); raise SystemExit("debía fallar")
except s.AlegraError as e: assert "documento" in str(e)
os.environ["ALEGRA_TOKEN"] = ""
assert not s.configurado()
print("TODAS LAS PRUEBAS OK")
