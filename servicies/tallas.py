"""
Tallas de calzado disponibles en Taller El Obrero.

Para cambiar las tallas sin tocar código, define en .env / Render:
    TALLAS_ZAPATO=36,37,38,39,40,41,42,43
"""

import os

_POR_DEFECTO = "35,36,37,38,39,40,41,42,43,44"


def tallas_disponibles():
    crudo = os.getenv("TALLAS_ZAPATO", _POR_DEFECTO)
    return [t.strip() for t in crudo.split(",") if t.strip()]


def es_calzado(producto):
    """True si el producto (modelo o diccionario) es calzado."""

    def leer(campo):
        if isinstance(producto, dict):
            return producto.get(campo)
        return getattr(producto, campo, None)

    categoria = str(leer("categoria") or "").strip().lower()
    nombre = str(leer("nombre") or "").strip().lower()

    return (
        categoria in ("calzado", "zapato", "zapatos")
        or "zapato" in nombre
    )


def validar_talla(valor):
    """Devuelve (talla, error)."""

    talla = str(valor or "").strip()

    if not talla:
        return None, "Elige la talla del zapato."

    if talla not in tallas_disponibles():
        return None, "Esa talla no está disponible."

    return talla, None
