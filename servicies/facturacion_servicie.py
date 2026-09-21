from database.connection import db
from models.factura import Factura


class FacturacionService:

    def generar_numero(self):

        ultima_factura = (
            Factura.query
            .order_by(Factura.id.desc())
            .first()
        )

        if ultima_factura is None:

            numero = 1

        else:

            numero = ultima_factura.id + 1

        return f"FE-{numero:06d}"


    def generar_factura(self, pedido):

        numero = self.generar_numero()

        factura = Factura(

            pedido_id=pedido.id,

            numero=numero,

            prefijo="FE",

            subtotal=pedido.subtotal,

            iva=pedido.iva,

            total=pedido.total,

            estado_dian="PENDIENTE"

        )

        db.session.add(factura)

        db.session.commit()

        return factura