from flask import Blueprint, flash, redirect, session, url_for

from database.connection import db
from models.factura import Factura
from servicies.alegra_service import AlegraError, configurado, emitir_factura

alegra = Blueprint("alegra", __name__)


@alegra.route("/emitir/<int:factura_id>", methods=["POST"])
def emitir(factura_id):

    if session.get("rol") != "administrador":
        flash("No tienes permisos para emitir facturas.", "error")
        return redirect(url_for("principal.inicio"))

    destino = redirect(
        url_for("facturacion.detalle_factura", factura_id=factura_id)
    )

    factura = Factura.query.get_or_404(factura_id)

    if not configurado():
        flash(
            "Alegra no está configurado: faltan ALEGRA_EMAIL y ALEGRA_TOKEN.",
            "error"
        )
        return destino

    try:
        resultado = emitir_factura(factura)
        db.session.commit()

    except AlegraError as error:
        db.session.rollback()
        flash(f"No se pudo emitir en Alegra: {error}", "error")
        return destino

    except Exception as error:
        db.session.rollback()
        print("ERROR INESPERADO AL EMITIR EN ALEGRA:", error)
        flash("Error inesperado al emitir la factura. Revisa los registros.", "error")
        return destino

    if resultado.get("advertencia"):
        flash(resultado["advertencia"], "warning")
    elif resultado.get("ya_emitida"):
        flash("Esta factura ya estaba emitida.", "success")
    elif resultado.get("cufe"):
        flash("Factura emitida y aceptada. CUFE guardado.", "success")
    else:
        flash(
            "Factura creada en Alegra; todavía no tiene CUFE (la DIAN la está procesando). "
            "Vuelve a pulsar el botón en unos minutos.",
            "success"
        )

    return destino