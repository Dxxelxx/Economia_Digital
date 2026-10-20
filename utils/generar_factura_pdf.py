from io import BytesIO
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def formato_pesos(valor):
    """
    Convierte un valor numérico a formato de pesos colombianos.
    """
    valor = Decimal(str(valor or 0))
    valor_entero = int(valor)

    return f"$ {valor_entero:,.0f}".replace(",", ".")


def generar_factura_pdf(factura):
    """
    Genera un PDF a partir de una instancia del modelo Factura.

    Retorna un objeto BytesIO listo para descargar con Flask.
    """

    archivo = BytesIO()

    documento = SimpleDocTemplate(
        archivo,
        pagesize=letter,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "TituloFactura",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        textColor=colors.HexColor("#7A4B24"),
        spaceAfter=10
    )

    subtitulo = ParagraphStyle(
        "SubtituloFactura",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.HexColor("#666666")
    )

    estilo_derecha = ParagraphStyle(
        "Derecha",
        parent=estilos["Normal"],
        alignment=TA_RIGHT
    )

    contenido = []

    # Encabezado
    contenido.append(
        Paragraph("TALLER EL OBRERO", titulo)
    )

    contenido.append(
        Paragraph("Documento generado por el sistema de gestión", subtitulo)
    )

    contenido.append(Spacer(1, 25))

    # Número y fecha
    numero_factura = factura.numero or str(factura.id)

    fecha = (
        factura.fecha.strftime("%d/%m/%Y %H:%M")
        if factura.fecha
        else "No registrada"
    )

    datos_encabezado = [
        [
            Paragraph("<b>Factura:</b>", estilos["Normal"]),
            Paragraph(str(numero_factura), estilos["Normal"]),
            Paragraph("<b>Fecha:</b>", estilos["Normal"]),
            Paragraph(fecha, estilos["Normal"])
        ],
        [
            Paragraph("<b>Pedido:</b>", estilos["Normal"]),
            Paragraph(str(factura.pedido_id), estilos["Normal"]),
            Paragraph("<b>Estado:</b>", estilos["Normal"]),
            Paragraph(
                str(factura.estado_dian or "PENDIENTE"),
                estilos["Normal"]
            )
        ]
    ]

    tabla_encabezado = Table(
        datos_encabezado,
        colWidths=[2.5 * cm, 4 * cm, 2 * cm, 5 * cm]
    )

    tabla_encabezado.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F0E6")),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D8C3A5")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8C3A5")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ])
    )

    contenido.append(tabla_encabezado)
    contenido.append(Spacer(1, 25))

    # Información del pedido
    pedido = factura.pedido

    contenido.append(
        Paragraph("DETALLE DEL PEDIDO", estilos["Heading2"])
    )

    if pedido:
        datos_pedido = [
            ["Concepto", "Detalle"],
            ["Número de pedido", str(pedido.id)],
            ["Cantidad", str(pedido.cantidad)],
            ["Estado del pedido", str(pedido.estado)],
        ]

        if pedido.fecha_pedido:
            datos_pedido.append([
                "Fecha del pedido",
                pedido.fecha_pedido.strftime("%d/%m/%Y %H:%M")
            ])

        tabla_pedido = Table(
            datos_pedido,
            colWidths=[6 * cm, 7.5 * cm]
        )

        tabla_pedido.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7A4B24")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8C3A5")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ])
        )

        contenido.append(tabla_pedido)

    contenido.append(Spacer(1, 25))

    # Valores económicos de la factura
    contenido.append(
        Paragraph("RESUMEN ECONÓMICO", estilos["Heading2"])
    )

    datos_valores = [
        ["Concepto", "Valor"],
        ["Subtotal", formato_pesos(factura.subtotal)],
        ["IVA", formato_pesos(factura.iva)],
        ["TOTAL", formato_pesos(factura.total)],
    ]

    tabla_valores = Table(
        datos_valores,
        colWidths=[9 * cm, 4.5 * cm]
    )

    tabla_valores.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7A4B24")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8C3A5")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F7F0E6")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])
    )

    contenido.append(tabla_valores)
    contenido.append(Spacer(1, 30))

    # Estado de validación
    estado = (factura.estado_dian or "PENDIENTE").upper()

    if estado == "ACEPTADA" and factura.cufe:
        texto_estado = (
            "Estado de validación: ACEPTADA. "
            "El documento dispone de un CUFE registrado en el sistema."
        )
    else:
        texto_estado = (
            "Documento generado por el sistema. "
            "No constituye por sí solo evidencia de validación electrónica "
            "por la DIAN."
        )

    contenido.append(
        Paragraph(texto_estado, estilos["Normal"])
    )

    contenido.append(Spacer(1, 20))

    contenido.append(
        Paragraph(
            "Taller El Obrero - Sistema de gestión de pedidos y facturación",
            subtitulo
        )
    )

    documento.build(contenido)

    archivo.seek(0)

    return archivo