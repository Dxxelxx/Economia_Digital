from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)
from datetime import datetime

from database.connection import db
from models.produccion import Produccion
from models.pedido import Pedido


produccion = Blueprint(
    "produccion",
    __name__
)


# =========================================================
# VERIFICAR QUE EL USUARIO SEA ADMINISTRADOR
# =========================================================

def administrador_requerido():
    if "usuario_id" not in session:
        return redirect(
            url_for(
                "auth.login",
                next=url_for("produccion.mostrar_produccion")
            )
        )

    if session.get("rol") != "administrador":
        flash(
            "No tienes permisos para acceder al módulo de producción.",
            "error"
        )
        return redirect(url_for("cliente.inicio"))

    return None


# =========================================================
# ESTADOS DE PRODUCCIÓN
# =========================================================

ESTADOS_PRODUCCION = [
    "Pendiente",
    "En producción",
    "En pausa",
    "Finalizada",
    "Cancelada"
]


# =========================================================
# EQUIVALENCIA ENTRE ESTADOS DE PRODUCCIÓN Y PEDIDOS
# =========================================================

ESTADOS_PEDIDO = {
    "Pendiente": "Aceptado",
    "En producción": "En producción",
    "En pausa": "En producción",
    "Finalizada": "Listo para enviar",
    "Cancelada": "Cancelado"
}


# =========================================================
# LISTAR PRODUCCIÓN
# =========================================================

@produccion.route("/")
def mostrar_produccion():
    acceso = administrador_requerido()

    if acceso:
        return acceso

    busqueda = request.args.get("buscar", "").strip()
    estado_filtro = request.args.get("estado", "").strip()

    consulta = (
        db.session.query(Produccion)
        .join(Pedido, Produccion.pedido_id == Pedido.id)
    )

    if estado_filtro in ESTADOS_PRODUCCION:
        consulta = consulta.filter(
            Produccion.estado == estado_filtro
        )

    if busqueda:
        if busqueda.isdigit():
            consulta = consulta.filter(
                Pedido.id == int(busqueda)
            )
        else:
            consulta = consulta.filter(
                db.cast(Pedido.id, db.String).ilike(
                    f"%{busqueda}%"
                )
            )

    producciones = consulta.order_by(
        Produccion.fecha_creacion.desc()
    ).all()

    # Crear registros de producción para pedidos aceptados
    # que todavía no tienen uno.
    pedidos_aceptados = Pedido.query.filter(
        Pedido.estado.in_([
            "Aceptado",
            "En producción"
        ])
    ).all()

    cambios = False

    for pedido in pedidos_aceptados:
        registro = Produccion.query.filter_by(
            pedido_id=pedido.id
        ).first()

        if registro is None:
            registro = Produccion(
                pedido_id=pedido.id,
                estado=(
                    "En producción"
                    if pedido.estado == "En producción"
                    else "Pendiente"
                )
            )

            db.session.add(registro)
            cambios = True

    if cambios:
        db.session.commit()

        # Volver a consultar para incluir los registros nuevos.
        consulta = (
            db.session.query(Produccion)
            .join(Pedido, Produccion.pedido_id == Pedido.id)
        )

        if estado_filtro in ESTADOS_PRODUCCION:
            consulta = consulta.filter(
                Produccion.estado == estado_filtro
            )

        if busqueda:
            if busqueda.isdigit():
                consulta = consulta.filter(
                    Pedido.id == int(busqueda)
                )
            else:
                consulta = consulta.filter(
                    db.cast(Pedido.id, db.String).ilike(
                        f"%{busqueda}%"
                    )
                )

        producciones = consulta.order_by(
            Produccion.fecha_creacion.desc()
        ).all()

    total_producciones = Produccion.query.count()

    pendientes = Produccion.query.filter_by(
        estado="Pendiente"
    ).count()

    en_produccion = Produccion.query.filter_by(
        estado="En producción"
    ).count()

    finalizadas = Produccion.query.filter_by(
        estado="Finalizada"
    ).count()

    return render_template(
        "admin/produccion.html",
        producciones=producciones,
        estados_produccion=ESTADOS_PRODUCCION,
        estado_filtro=estado_filtro,
        busqueda=busqueda,
        total_producciones=total_producciones,
        pendientes=pendientes,
        en_produccion=en_produccion,
        finalizadas=finalizadas
    )


# =========================================================
# ACTUALIZAR ESTADO DE PRODUCCIÓN
# =========================================================

@produccion.route("/<int:produccion_id>/estado", methods=["POST"])
def actualizar_estado(produccion_id):
    acceso = administrador_requerido()

    if acceso:
        return acceso

    registro = db.session.get(
        Produccion,
        produccion_id
    )

    if registro is None:
        flash(
            "No se encontró el registro de producción.",
            "error"
        )
        return redirect(
            url_for("produccion.mostrar_produccion")
        )

    nuevo_estado = request.form.get(
        "estado",
        ""
    ).strip()

    if nuevo_estado not in ESTADOS_PRODUCCION:
        flash(
            "El estado de producción seleccionado no es válido.",
            "error"
        )
        return redirect(
            url_for("produccion.mostrar_produccion")
        )

    if registro.estado == "Cancelada":
        flash(
            "No puedes modificar una producción cancelada.",
            "error"
        )
        return redirect(
            url_for("produccion.mostrar_produccion")
        )

    if registro.estado == "Finalizada":
        flash(
            "La producción ya está finalizada.",
            "error"
        )
        return redirect(
            url_for("produccion.mostrar_produccion")
        )

    pedido = db.session.get(
        Pedido,
        registro.pedido_id
    )

    if pedido is None:
        flash(
            "El pedido asociado ya no existe.",
            "error"
        )
        return redirect(
            url_for("produccion.mostrar_produccion")
        )

    ahora = datetime.utcnow()

    # Registrar la fecha de inicio la primera vez
    # que la producción comienza.
    if nuevo_estado == "En producción":
        if registro.fecha_inicio is None:
            registro.fecha_inicio = ahora

    # Registrar la finalización.
    if nuevo_estado == "Finalizada":
        if registro.fecha_inicio is None:
            registro.fecha_inicio = ahora

        registro.fecha_finalizacion = ahora

    if nuevo_estado == "Cancelada":
        pedido.estado = "Cancelado"

    elif nuevo_estado == "Finalizada":
        pedido.estado = "Listo para enviar"

    elif nuevo_estado == "En producción":
        pedido.estado = "En producción"

    elif nuevo_estado == "Pendiente":
        pedido.estado = "Aceptado"

    elif nuevo_estado == "En pausa":
        pedido.estado = "En producción"

    registro.estado = nuevo_estado

    db.session.commit()

    flash(
        f"Producción del pedido #{pedido.id} actualizada correctamente.",
        "success"
    )

    return redirect(
        url_for("produccion.mostrar_produccion")
    )


# =========================================================
# ACTUALIZAR OBSERVACIONES
# =========================================================

@produccion.route(
    "/<int:produccion_id>/observaciones",
    methods=["POST"]
)
def actualizar_observaciones(produccion_id):
    acceso = administrador_requerido()

    if acceso:
        return acceso

    registro = db.session.get(
        Produccion,
        produccion_id
    )

    if registro is None:
        flash(
            "No se encontró el registro de producción.",
            "error"
        )
        return redirect(
            url_for("produccion.mostrar_produccion")
        )

    observaciones = request.form.get(
        "observaciones",
        ""
    ).strip()

    registro.observaciones = observaciones or None

    db.session.commit()

    flash(
        "Las observaciones se guardaron correctamente.",
        "success"
    )

    return redirect(
        url_for("produccion.mostrar_produccion")
    )