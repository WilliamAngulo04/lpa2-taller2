from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import requests
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_RIGHT
from xml.sax.saxutils import escape
from urllib.parse import quote
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
BACKEND_URL = os.getenv('BACKEND_API_URL', os.getenv('BACKEND_URL', 'http://backend:8000'))
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

COLOR_PRIMARIO = colors.HexColor('#2E7D32')


def moneda(valor):
    return f"{valor:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')


def texto(valor):
    # Escapar para el mini-lenguaje XML de Paragraph y conservar saltos de línea
    return escape(str(valor)).replace('\n', '<br/>')


def construir_pdf(factura):
    # Crear buffer y doc para la creación del PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Factura {factura['numero_factura']}",
    )
    ancho = doc.width
    styles = getSampleStyleSheet()
    normal = styles['Normal']
    titulo = ParagraphStyle('Titulo', parent=styles['Title'], textColor=COLOR_PRIMARIO, alignment=0)
    subtitulo = ParagraphStyle('Subtitulo', parent=styles['Heading3'], textColor=COLOR_PRIMARIO, spaceAfter=4)
    derecha = ParagraphStyle('Derecha', parent=normal, alignment=TA_RIGHT)
    elements = []

    # Adicionar el Título, ID
    encabezado = Table(
        [[Paragraph('FACTURA', titulo),
          Paragraph(f"<b>N.º:</b> {texto(factura['numero_factura'])}<br/>"
                    f"<b>Fecha de emisión:</b> {texto(factura['fecha_emision'])}", derecha)]],
        colWidths=[ancho * 0.5, ancho * 0.5],
    )
    encabezado.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, 0), 2, COLOR_PRIMARIO),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(encabezado)
    elements.append(Spacer(1, 8 * mm))

    # Agregar Información de la Empresa
    empresa = factura['empresa']
    bloque_empresa = [
        Paragraph('Emisor', subtitulo),
        Paragraph(f"<b>{texto(empresa['nombre'])}</b>", normal),
        Paragraph(texto(empresa['direccion']), normal),
        Paragraph(f"Tel: {texto(empresa['telefono'])}", normal),
        Paragraph(f"Email: {texto(empresa['email'])}", normal),
    ]

    # Agregar Información del Cliente
    cliente = factura['cliente']
    bloque_cliente = [
        Paragraph('Facturar a', subtitulo),
        Paragraph(f"<b>{texto(cliente['nombre'])}</b>", normal),
        Paragraph(texto(cliente['direccion']), normal),
        Paragraph(f"Tel: {texto(cliente['telefono'])}", normal),
    ]

    partes = Table([[bloque_empresa, bloque_cliente]], colWidths=[ancho * 0.5, ancho * 0.5])
    partes.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
    ]))
    elements.append(partes)
    elements.append(Spacer(1, 10 * mm))

    # Adicionar el Detalle de la Factura: cantidad, descripción, precio unitario y total
    filas = [['Cant.', 'Descripción', 'Precio unitario', 'Total']]
    for item in factura['detalle']:
        filas.append([
            str(item['cantidad']),
            Paragraph(texto(item['descripcion']), normal),
            moneda(item['precio_unitario']),
            moneda(item['total']),
        ])

    detalle = Table(filas, colWidths=[ancho * 0.1, ancho * 0.5, ancho * 0.2, ancho * 0.2], repeatRows=1)
    detalle.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARIO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F8E9')]),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(detalle)
    elements.append(Spacer(1, 6 * mm))

    # Adicionar Subtotal, impuesto y Total
    totales = Table(
        [
            ['Subtotal', moneda(factura['subtotal'])],
            ['IVA (21%)', moneda(factura['impuesto'])],
            ['TOTAL', moneda(factura['total'])],
        ],
        colWidths=[ancho * 0.2, ancho * 0.2],
        hAlign='RIGHT',
    )
    totales.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 1, COLOR_PRIMARIO),
        ('TEXTCOLOR', (0, -1), (-1, -1), COLOR_PRIMARIO),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(totales)

    # Generar el doc y limpiar el buffer
    doc.build(elements)
    buffer.seek(0)
    return buffer


def error(mensaje, status):
    # Las peticiones desde app.js reciben JSON; el formulario clásico vuelve al inicio con un mensaje
    if request.headers.get('X-Requested-With') == 'fetch':
        return jsonify(error=mensaje), status
    flash(mensaje)
    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return {'status': 'ok', 'servicio': 'Frontend de Facturas'}


@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    id_factura = request.form.get('id_factura', '').strip()
    if not id_factura:
        return error('Debe ingresar un número de factura', 400)

    try:
        response = requests.get(f'{BACKEND_URL}/facturas/v1/{quote(id_factura, safe="")}', timeout=10)
    except requests.exceptions.RequestException:
        return error('Error de conexión con el servidor de facturas', 503)

    if response.status_code == 422:
        return error('Número de factura inválido: use solo letras, números, guiones (máx. 50)', 400)
    if response.status_code != 200:
        return error(f'Factura "{id_factura}" no encontrada', 404)

    try:
        buffer = construir_pdf(response.json())
    except Exception as e:
        app.logger.exception('Error generando el PDF')
        return error(f'Error generando el PDF: {e}', 500)

    # Retornar a la página el PDF para visualizar y descargar
    descargar = request.form.get('descargar') == '1'
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=descargar,
        download_name=f'factura_{id_factura}.pdf',
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=DEBUG)
