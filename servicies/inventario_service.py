from database.connection import db
from models.inventario import Inventario


def descontar_material(
    material_id,
    cantidad
):

    material = db.session.get(
        Inventario,
        material_id
    )

    if material is None:

        return False, "Material no encontrado."

    if material.cantidad < cantidad:

        return False, "No hay suficiente inventario."

    material.cantidad -= cantidad

    db.session.commit()

    return True, "Inventario actualizado."


def agregar_material(
    material_id,
    cantidad
):

    material = db.session.get(
        Inventario,
        material_id
    )

    if material is None:

        return False, "Material no encontrado."

    material.cantidad += cantidad

    db.session.commit()

    return True, "Inventario actualizado."