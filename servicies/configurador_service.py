"""
Catálogo, validación y precio de los diseños del configurador 3D.

Este módulo es la ÚNICA fuente de verdad de opciones y precios:
el navegador recibe una copia para mostrar el precio estimado, pero
el precio que se cobra siempre se recalcula aquí, en el servidor.

Para cambiar un precio u ofrecer una opción nueva, edita las tablas
de abajo (PRODUCTOS, MATERIALES, HERRAJES, COLORES).
"""

import re


# ==========================================================
# TABLAS DE OPCIONES Y PRECIOS (en pesos colombianos)
# ==========================================================

IVA = 0.19

EXTRA_INICIALES = 15000

COLORES = [
    ("#6b4226", "Café artesanal"),
    ("#111111", "Negro"),
    ("#8b5e3c", "Cuero claro"),
    ("#7d1f27", "Vino"),
    ("#294c3a", "Verde artesanal"),
    ("#d9c7a3", "Arena"),
    ("#1f3a5f", "Azul noche"),
    ("#f2ece1", "Marfil"),
]

# (valor, nombre, extra)
MATERIALES = [
    ("cuero", "Cuero", 0),
    ("ante", "Ante", 30000),
    ("sintetico", "Sintético", -20000),
]

HERRAJES = [
    ("dorado", "Dorado", 15000),
    ("plateado", "Plateado", 0),
    ("negro", "Negro", 0),
]

PRODUCTOS = {
    "zapato": {
        "nombre": "Zapato artesanal",
        "categoria": "Calzado",
        "base": 320000,
        "etiqueta_estilo": "Suela",
        "estilos": [
            ("clasica", "Clásica", 0),
            ("premium", "Premium", 25000),
            ("urbana", "Urbana", 40000),
        ],
        "estilo_defecto": "clasica",
    },
    "bolso": {
        "nombre": "Bolso artesanal",
        "categoria": "Bolsos",
        "base": 280000,
        "etiqueta_estilo": "Asas",
        "estilos": [
            ("corta", "Asa corta", 0),
            ("larga", "Asa larga", 25000),
            ("doble", "Doble asa", 40000),
        ],
        "estilo_defecto": "corta",
    },
    "sombrero": {
        "nombre": "Sombrero artesanal",
        "categoria": "Sombreros",
        "base": 180000,
        "etiqueta_estilo": "Ala",
        "estilos": [
            ("corta", "Ala corta", 0),
            ("media", "Ala media", 10000),
            ("ancha", "Ala ancha", 25000),
        ],
        "estilo_defecto": "media",
    },
}

DEFECTO = {
    "producto": "zapato",
    "color": "#6b4226",
    "colorSecundario": "#111111",
    "material": "cuero",
    "herrajes": "dorado",
}

PATRON_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
PATRON_INICIALES = re.compile(r"^[A-Z0-9ÁÉÍÓÚÑÜ]{0,3}$")


# ==========================================================
# CATÁLOGO PARA EL NAVEGADOR
# ==========================================================

def _opciones(tabla):
    return [
        {"valor": valor, "nombre": nombre, "extra": extra}
        for valor, nombre, extra in tabla
    ]


def catalogo_para_cliente():
    """Estructura JSON que usa el configurador en el navegador."""

    return {
        "iva": IVA,
        "extra_iniciales": EXTRA_INICIALES,
        "colores": [{"hex": h, "nombre": n} for h, n in COLORES],
        "materiales": _opciones(MATERIALES),
        "herrajes": _opciones(HERRAJES),
        "productos": {
            clave: {
                "nombre": p["nombre"],
                "base": p["base"],
                "etiqueta_estilo": p["etiqueta_estilo"],
                "estilos": _opciones(p["estilos"]),
                "estilo_defecto": p["estilo_defecto"],
            }
            for clave, p in PRODUCTOS.items()
        },
        "defecto": DEFECTO,
    }


# ==========================================================
# AYUDAS
# ==========================================================

def _buscar(tabla, valor):
    for fila in tabla:
        if fila[0] == valor:
            return fila
    return None


def nombre_de_color(hex_color):
    for h, nombre in COLORES:
        if h.lower() == hex_color.lower():
            return nombre

    return "Personalizado"


def calcular_precio_unitario(diseno):
    """Precio de UNA unidad (antes de IVA) para un diseño ya validado."""

    producto = PRODUCTOS[diseno["producto"]]

    total = producto["base"]
    total += _buscar(MATERIALES, diseno["material"])[2]
    total += _buscar(producto["estilos"], diseno["estilo"])[2]
    total += _buscar(HERRAJES, diseno["herrajes"])[2]

    if diseno["iniciales"]:
        total += EXTRA_INICIALES

    return total


# ==========================================================
# VALIDACIÓN
# ==========================================================

def validar_diseno(datos):
    """
    Valida lo que envía el navegador. Devuelve (diseno, error):
      - diseno: diccionario limpio y con el precio calculado, o None
      - error:  mensaje para el cliente, o None
    """

    if not isinstance(datos, dict):
        return None, "No se recibió un diseño válido."

    producto = str(datos.get("producto", ""))

    if producto not in PRODUCTOS:
        return None, "Elige un producto válido."

    definicion = PRODUCTOS[producto]

    colores = {}

    for campo, etiqueta in (
        ("color", "principal"),
        ("colorSecundario", "secundario"),
    ):
        valor = str(datos.get(campo, ""))

        if not PATRON_COLOR.match(valor):
            return None, f"El color {etiqueta} no es válido."

        colores[campo] = valor.lower()

    material = str(datos.get("material", ""))

    if _buscar(MATERIALES, material) is None:
        return None, "Elige un material válido."

    estilo = str(datos.get("estilo", ""))

    if _buscar(definicion["estilos"], estilo) is None:
        return None, f"Elige una opción válida de {definicion['etiqueta_estilo'].lower()}."

    herrajes = str(datos.get("herrajes", ""))

    if _buscar(HERRAJES, herrajes) is None:
        return None, "Elige unos herrajes válidos."

    iniciales = str(datos.get("iniciales", "")).strip().upper()

    if not PATRON_INICIALES.match(iniciales):
        return None, "Las iniciales deben tener máximo 3 letras o números."

    diseno = {
        "producto": producto,
        "color": colores["color"],
        "colorSecundario": colores["colorSecundario"],
        "material": material,
        "estilo": estilo,
        "herrajes": herrajes,
        "iniciales": iniciales,
    }

    diseno["precio_unitario"] = calcular_precio_unitario(diseno)

    return diseno, None


# ==========================================================
# TEXTOS PARA GUARDAR EN LA BASE DE DATOS
# ==========================================================

def describir_diseno(diseno):
    """
    Textos legibles para los campos de la tabla Configuracion
    (color, material, suela, herrajes, iniciales).
    """

    definicion = PRODUCTOS[diseno["producto"]]

    color = (
        f"{nombre_de_color(diseno['color'])} {diseno['color']} / "
        f"{nombre_de_color(diseno['colorSecundario'])} "
        f"{diseno['colorSecundario']}"
    )

    estilo = _buscar(definicion["estilos"], diseno["estilo"])[1]

    return {
        "color": color[:50],
        "material": _buscar(MATERIALES, diseno["material"])[1],
        "suela": f"{definicion['etiqueta_estilo']}: {estilo}",
        "herrajes": _buscar(HERRAJES, diseno["herrajes"])[1],
        "iniciales": diseno["iniciales"],
    }
