"""
Comprueba tus credenciales de Alegra y muestra los ids que necesitas.
Uso (en tu PC, con ALEGRA_EMAIL y ALEGRA_TOKEN en tu .env):
    python probar_alegra.py
"""
from dotenv import load_dotenv

load_dotenv()

from servicies.alegra_service import AlegraError, llamar

try:
    print("== Resoluciones de numeración (ALEGRA_NUMBER_TEMPLATE_ID) ==")
    for p in llamar("GET", "/number-templates"):
        print(f'  id={p.get("id")}  nombre={p.get("name")}  prefijo={p.get("prefix")}  '
              f'documento={p.get("documentType")}  activa={p.get("status")}')

    print("\n== Impuestos (ALEGRA_IVA_TAX_ID: busca IVA 19 %) ==")
    for t in llamar("GET", "/taxes"):
        print(f'  id={t.get("id")}  nombre={t.get("name")}  porcentaje={t.get("percentage")}')

    print("\nConexión correcta.")
except AlegraError as error:
    print("ERROR:", error)
