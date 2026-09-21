def calcular_precio(
    precio_base,
    material=None,
    suela=None,
    herrajes=None,
    iniciales=None
):

    precio = float(precio_base)

    # Valores de demostración.
    # Posteriormente los manejaremos
    # desde PostgreSQL.

    if material == "cuero_vegetal":
        precio += 30000

    if suela == "reciclada":
        precio += 20000

    if herrajes == "dorados":
        precio += 10000

    if iniciales:
        precio += 15000

    return precio