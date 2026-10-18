from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from decimal import Decimal, InvalidOperation

from database.connection import db
from models.inventario import Inventario


inventario = Blueprint(
    "inventario",
    __name__
)


# =====================================================
# ESTABLECER SI EL USUARIO ES ADMINISTRADOR
# =====================================================

def administrador_requerido():

    if "usuario_id" not in session:

        return redirect(
            url_for(
                "auth.login",
                next=url_for("inventario.mostrar_inventario")
            )
        )

    if session.get("rol") != "administrador":

        flash(
            "No tienes permisos para acceder al inventario.",
            "error"
        )

        if session.get("rol") == "cliente":
            return redirect(url_for("cliente.inicio"))

        return redirect(url_for("auth.login"))

    return None


# =====================================================
# CONVERTIR Y VALIDAR CANTIDADES
# =====================================================

def convertir_cantidad(valor):

    try:

        cantidad = Decimal(str(valor).strip())

        if not cantidad.is_finite():
            raise ValueError

        if cantidad < 0:
            raise ValueError

        if cantidad > Decimal("99999999.99"):
            raise ValueError

        if cantidad.as_tuple().exponent < -2:
            raise ValueError

        return cantidad

    except (InvalidOperation, ValueError, TypeError):

        return None


# =====================================================
# MOSTRAR INVENTARIO
# =====================================================

@inventario.route("/")
def mostrar_inventario():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    busqueda = request.args.get(
        "buscar",
        ""
    ).strip()

    consulta = Inventario.query

    if busqueda:

        consulta = consulta.filter(
            or_(
                Inventario.material.ilike(f"%{busqueda}%"),
                Inventario.descripcion.ilike(f"%{busqueda}%")
            )
        )

    materiales = consulta.order_by(
        Inventario.material.asc()
    ).all()

    total_materiales = Inventario.query.count()

    materiales_bajos = Inventario.query.filter(
        Inventario.cantidad <= Inventario.minimo
    ).count()

    materiales_agotados = Inventario.query.filter(
        Inventario.cantidad <= 0
    ).count()

    return render_template(
        "admin/inventario.html",
        materiales=materiales,
        busqueda=busqueda,
        total_materiales=total_materiales,
        materiales_bajos=materiales_bajos,
        materiales_agotados=materiales_agotados
    )


# =====================================================
# REGISTRAR MATERIAL NUEVO
# =====================================================

@inventario.route(
    "/agregar",
    methods=["POST"]
)
def agregar_material():

    acceso = administrador_requerido()

    if acceso:
        return acceso

    material = request.form.get(
        "material",
        ""
    ).strip()

    descripcion = request.form.get(
        "descripcion",
        ""
    ).strip()

    unidad = request.form.get(
        "unidad",
        "unidad"
    ).strip()

    cantidad = convertir_cantidad(
        request.form.get("cantidad", "")
    )

    minimo = convertir_cantidad(
        request.form.get("minimo", "0")
    )

    if not material:

        flash(
            "El nombre del material es obligatorio.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    if len(material) > 100:

        flash(
            "El nombre del material no puede superar 100 caracteres.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    if len(unidad) > 30 or not unidad:

        flash(
            "Indica una unidad válida, por ejemplo: unidad, metro o kg.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    if cantidad is None or minimo is None:

        flash(
            "Las cantidades deben ser números positivos con máximo dos decimales.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    if len(descripcion) > 10000:

        flash(
            "La descripción es demasiado larga.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    existente = Inventario.query.filter(
        db.func.lower(Inventario.material) == material.lower()
    ).first()

    if existente:

        flash(
            "Ya existe un material con ese nombre. Puedes añadirle existencias desde la tabla.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    nuevo_material = Inventario(
        material=material,
        descripcion=descripcion or None,
        cantidad=cantidad,
        unidad=unidad,
        minimo=minimo
    )

    try:

        db.session.add(nuevo_material)
        db.session.commit()

        flash(
            f"El material '{material}' se registró correctamente.",
            "success"
        )

    except IntegrityError:

        db.session.rollback()

        flash(
            "No se pudo registrar el material. Comprueba si ya existe.",
            "error"
        )

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR AL REGISTRAR MATERIAL:",
            error
        )

        flash(
            "Ocurrió un error al registrar el material.",
            "error"
        )

    return redirect(url_for("inventario.mostrar_inventario"))


# =====================================================
# AÑADIR EXISTENCIAS
# =====================================================

@inventario.route(
    "/<int:material_id>/entrada",
    methods=["POST"]
)
def entrada_material(material_id):

    acceso = administrador_requerido()

    if acceso:
        return acceso

    material = db.session.get(
        Inventario,
        material_id
    )

    if material is None:

        flash(
            "El material seleccionado no existe.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    cantidad = convertir_cantidad(
        request.form.get("cantidad", "")
    )

    if cantidad is None or cantidad <= 0:

        flash(
            "La cantidad que vas a añadir debe ser mayor que cero.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    nueva_cantidad = Decimal(str(material.cantidad)) + cantidad

    if nueva_cantidad > Decimal("99999999.99"):

        flash(
            "La cantidad resultante supera el límite permitido.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    try:

        material.cantidad = nueva_cantidad

        db.session.commit()

        flash(
            f"Se añadieron {cantidad} {material.unidad} de {material.material}.",
            "success"
        )

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR AL AÑADIR EXISTENCIAS:",
            error
        )

        flash(
            "No fue posible actualizar las existencias.",
            "error"
        )

    return redirect(url_for("inventario.mostrar_inventario"))


# =====================================================
# CORREGIR EXISTENCIAS
# =====================================================

@inventario.route(
    "/<int:material_id>/actualizar",
    methods=["POST"]
)
def actualizar_material(material_id):

    acceso = administrador_requerido()

    if acceso:
        return acceso

    material = db.session.get(
        Inventario,
        material_id
    )

    if material is None:

        flash(
            "El material seleccionado no existe.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    cantidad = convertir_cantidad(
        request.form.get("cantidad", "")
    )

    minimo = convertir_cantidad(
        request.form.get("minimo", "")
    )

    if cantidad is None or minimo is None:

        flash(
            "Introduce cantidades válidas y no negativas.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    try:

        material.cantidad = cantidad
        material.minimo = minimo

        db.session.commit()

        flash(
            f"Se actualizaron las existencias de {material.material}.",
            "success"
        )

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR AL ACTUALIZAR INVENTARIO:",
            error
        )

        flash(
            "No fue posible guardar los cambios.",
            "error"
        )

    return redirect(url_for("inventario.mostrar_inventario"))


# =====================================================
# ELIMINAR MATERIAL
# =====================================================

@inventario.route(
    "/<int:material_id>/eliminar",
    methods=["POST"]
)
def eliminar_material(material_id):

    acceso = administrador_requerido()

    if acceso:
        return acceso

    material = db.session.get(
        Inventario,
        material_id
    )

    if material is None:

        flash(
            "El material que intentas eliminar no existe.",
            "error"
        )

        return redirect(url_for("inventario.mostrar_inventario"))

    try:

        nombre_material = material.material

        db.session.delete(material)
        db.session.commit()

        flash(
            f"El material '{nombre_material}' se eliminó del inventario.",
            "success"
        )

    except Exception as error:

        db.session.rollback()

        print(
            "ERROR AL ELIMINAR MATERIAL:",
            error
        )

        flash(
            "No se pudo eliminar el material. Comprueba si está relacionado con otros registros.",
            "error"
        )

    return redirect(url_for("inventario.mostrar_inventario"))