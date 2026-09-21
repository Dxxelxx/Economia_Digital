def calcular_entrega(
    cantidad,
    carga_taller=0
):

    dias = 5

    if cantidad <= 2:

        dias = 5

    elif cantidad <= 10:

        dias = 8

    else:

        dias = 12

    # Si el taller tiene más del 80%
    # de carga, agregamos tiempo.

    if carga_taller > 80:

        dias += 3

    return dias