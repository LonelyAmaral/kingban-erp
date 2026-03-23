"""PDF generator para orcamentos/pedidos usando ReportLab.

Layout baseado no desktop KING BAN:
1. Header: "Orcamento N° 02322" + data + logo
2. Info empresa: CNPJ, IE, endereco, vendedor
3. Box cliente: ID, nome, CNPJ/CPF, IE, endereco completo
4. Tabela itens: COD | PRODUTOS | QTDE | UN | VALOR UNIT | TOTAL
5. Totais: subtotal, frete, total
6. Observacoes: negociacao, disponibilidade, pagamento
7. Dados bancarios: Itau Ag 0168 CC 27284-7, PIX CNPJ
8. Linha de assinatura
"""

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# Colors (igual desktop)
GREEN_DARK = colors.HexColor('#1B5E20')
GREEN_HEADER = colors.HexColor('#2E7D32')
GRAY_LIGHT = colors.HexColor('#F5F5F5')


def format_currency(value: float) -> str:
    """Formata valor como moeda brasileira: R$ 1.234,56"""
    if value is None:
        value = 0
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def generate_order_pdf(
    order_data: dict,
    items: list,
    company: dict,
    client: dict,
) -> bytes:
    """
    Gera PDF de orcamento/pedido no formato KING BAN.

    Returns:
        bytes do PDF gerado (para StreamingResponse)
    """
    buffer = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buffer, pagesize=A4)

    # Margins
    left = 20 * mm
    right = width - 20 * mm
    top = height - 15 * mm
    content_width = right - left

    y = top

    # ================================================================
    # HEADER
    # ================================================================
    doc_type = order_data.get('document_type', 'ORCAMENTO')
    doc_label = 'Orcamento' if doc_type == 'ORCAMENTO' else 'Pedido'
    order_num = order_data.get('order_number', 0)
    order_date = order_data.get('date', date.today())
    if isinstance(order_date, str):
        try:
            order_date = date.fromisoformat(order_date)
        except ValueError:
            order_date = date.today()

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(GREEN_DARK)
    c.drawString(left, y, f"{doc_label} N\u00b0 {order_num:05d}")

    # Date on the right
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    date_str = order_date.strftime('%d/%m/%Y') if isinstance(order_date, date) else str(order_date)
    c.drawRightString(right, y, f"DATA: {date_str}")

    y -= 8 * mm

    # Company name
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(GREEN_DARK)
    company_name = company.get('name', 'KINGBAN COMERCIAL DE PROD. SANEANTES IMP. E EXP. LTDA')
    c.drawString(left, y, company_name)
    y -= 5 * mm

    # Separator line
    c.setStrokeColor(GREEN_DARK)
    c.setLineWidth(1.5)
    c.line(left, y, right, y)
    y -= 6 * mm

    # ================================================================
    # COMPANY + CLIENT INFO (two columns)
    # ================================================================
    col_mid = left + content_width * 0.45

    # Left column: Company info
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)

    company_info = [
        f"CNPJ: {company.get('cnpj', '96.453.840/0001-89')}",
        f"IE: {company.get('ie', '')}",
        f"COLETA/DEPOSITO: {company.get('address', 'Avare - SP')}",
        f"CEP {company.get('cep', '')} - {company.get('city', 'Avare')}/{company.get('state', 'SP')}",
        f"Vendedor: {order_data.get('salesperson_name', '')}",
        f"{doc_label} Num: {order_num:05d}",
        f"Forma de Pgto: {order_data.get('payment_method', 'PIX OU DEPOSITO BANCARIO')}",
    ]

    info_y = y
    for line in company_info:
        c.drawString(left, info_y, line)
        info_y -= 4 * mm

    # Right column: Client box
    box_x = col_mid + 5 * mm
    box_width = right - box_x
    box_height = len(company_info) * 4 * mm + 2 * mm

    # Client box border
    c.setStrokeColor(GREEN_DARK)
    c.setLineWidth(0.8)
    c.rect(box_x - 2 * mm, y - box_height + 2 * mm, box_width + 2 * mm, box_height)

    # Client header
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(GREEN_DARK)
    client_id = client.get('id', 0)
    c.drawString(box_x, y, f"CLIENTE: {client_id:05d}")

    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.black)
    client_lines = [
        client.get('name', client.get('nome', '')),
        f"CNPJ/CPF: {client.get('cnpj_cpf', '')}",
        f"IE: {client.get('ie', '')}",
        f"RUA: {client.get('address', client.get('endereco', ''))}",
        f"BAIRRO: {client.get('neighborhood', client.get('bairro', ''))}",
        f"CIDADE: {client.get('city', client.get('cidade', ''))}  UF: {client.get('state', client.get('estado', ''))}  CEP: {client.get('cep', '')}",
        f"CONTATO: {client.get('contact_phone', client.get('telefone', ''))}",
    ]

    client_y = y - 4 * mm
    for line in client_lines:
        c.drawString(box_x, client_y, line)
        client_y -= 3.5 * mm

    y = min(info_y, client_y) - 4 * mm

    # ================================================================
    # ITEMS TABLE
    # ================================================================
    col_widths = [15 * mm, 75 * mm, 15 * mm, 12 * mm, 25 * mm, 28 * mm]
    headers = ['COD.', 'PRODUTOS', 'QTDE', 'UN.', 'VALOR UNIT.', 'TOTAL']

    # Header background
    c.setFillColor(GREEN_HEADER)
    c.rect(left, y - 5 * mm, content_width, 6 * mm, fill=True)

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.white)
    x_pos = left + 1 * mm
    for i, (header, w) in enumerate(zip(headers, col_widths)):
        if i >= 4:
            c.drawRightString(x_pos + w - 1 * mm, y - 3.5 * mm, header)
        else:
            c.drawString(x_pos, y - 3.5 * mm, header)
        x_pos += w

    y -= 6 * mm

    # Item rows
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)

    for idx, item in enumerate(items):
        if y < 60 * mm:
            c.showPage()
            y = height - 20 * mm

        # Alternating row color
        if idx % 2 == 0:
            c.setFillColor(GRAY_LIGHT)
            c.rect(left, y - 4 * mm, content_width, 5 * mm, fill=True)
            c.setFillColor(colors.black)

        x_pos = left + 1 * mm
        row_data = [
            str(item.get('product_code', '')),
            str(item.get('product_name', '')),
            str(item.get('quantity', '')),
            str(item.get('unit', 'UN')),
            format_currency(item.get('unit_price', 0)),
            format_currency(item.get('total', 0)),
        ]

        c.setFont("Helvetica", 7.5)
        for i, (val, w) in enumerate(zip(row_data, col_widths)):
            if i == 1 and len(val) > 50:
                val = val[:47] + '...'
            if i >= 4:
                c.drawRightString(x_pos + w - 1 * mm, y - 3 * mm, val)
            else:
                c.drawString(x_pos, y - 3 * mm, val)
            x_pos += w

        y -= 5 * mm

    # Bottom line
    c.setStrokeColor(GREEN_DARK)
    c.setLineWidth(0.5)
    c.line(left, y, right, y)
    y -= 6 * mm

    # ================================================================
    # TOTALS
    # ================================================================
    totals_x = right - 55 * mm

    c.setFont("Helvetica", 9)
    subtotal = order_data.get('subtotal', 0) or 0
    freight = order_data.get('freight_value', 0) or 0
    total = order_data.get('total', 0) or 0

    c.setFillColor(colors.black)
    c.drawString(totals_x, y, "VALOR TOTAL PROD. R$:")
    c.drawRightString(right, y, format_currency(subtotal))
    y -= 4.5 * mm

    c.drawString(totals_x, y, "SUB. TOTAL R$:")
    c.drawRightString(right, y, format_currency(subtotal))
    y -= 4.5 * mm

    if freight > 0:
        c.drawString(totals_x, y, "VALOR DO FRETE:")
        c.drawRightString(right, y, format_currency(freight))
        y -= 4.5 * mm

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(GREEN_DARK)
    c.drawString(totals_x, y, "TOTAL R$:")
    c.drawRightString(right, y, format_currency(total))
    y -= 8 * mm

    # ================================================================
    # OBSERVATIONS
    # ================================================================
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(left, y, "OBSERVACOES:")
    y -= 5 * mm

    c.setFont("Helvetica", 7.5)

    nf_type = order_data.get('nf_type', '')
    availability = order_data.get('availability', 'A PRONTA ENTREGA')
    payment_terms = order_data.get('payment_terms', '')
    observations = order_data.get('observations', '')

    obs_lines = []
    if nf_type:
        obs_lines.append(f"NEGOCIACAO: {nf_type}")
    if availability:
        obs_lines.append(f"DISPONIBILIDADE: {availability}")

    obs_lines.append("")
    obs_lines.append("CONDICAO DE PAGAMENTO:")
    if payment_terms:
        obs_lines.append(f"  {payment_terms}")
    else:
        obs_lines.append("  Opcao 1: A VISTA, via transferencia bancaria, PIX ou deposito em conta corrente")
        obs_lines.append("  Opcao 2: Sinal de 30% para programacao do pedido + 70% apos pedido pronto")

    # Bank details
    obs_lines.append("")
    bank = company.get('bank_name', 'ITAU')
    agency = company.get('bank_agency', '0168')
    account = company.get('bank_account', '27284-7')
    pix = company.get('pix_key', '96.453.840/0001-89')
    obs_lines.append(f"BANCO {bank} - Agencia: {agency} - Conta corrente: {account}")
    obs_lines.append(f"CHAVE PIX: {pix} (CNPJ)")

    obs_lines.append("")
    obs_lines.append("NAO trabalhamos com BOLETO.")
    obs_lines.append("Liberacao do(s) produto(s) somente apos confirmacao do pagamento integral.")

    # DIFAL
    difal_value = order_data.get('difal_value', 0) or 0
    if difal_value > 0:
        obs_lines.append("")
        obs_lines.append(f"* IMPOSTO: ICMS DIFAL no valor de {format_currency(difal_value)} a ser pago pelo comprador.")

    obs_lines.append("")
    obs_lines.append("* FRETE: Por conta do comprador. Seguro de transporte por conta do comprador.")

    if observations:
        obs_lines.append("")
        obs_lines.append(observations)

    for line in obs_lines:
        if y < 25 * mm:
            c.showPage()
            y = height - 20 * mm
        c.drawString(left, y, line)
        y -= 3.5 * mm

    # ================================================================
    # SIGNATURE LINE
    # ================================================================
    y -= 8 * mm
    if y < 30 * mm:
        c.showPage()
        y = height - 40 * mm

    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    sig_width = 80 * mm
    sig_x = left + (content_width - sig_width) / 2
    c.line(sig_x, y, sig_x + sig_width, y)
    y -= 4 * mm

    c.setFont("Helvetica", 8)
    c.drawCentredString(left + content_width / 2, y, "De acordo: (Nome Completo e CPF)")

    # Save
    c.save()
    buffer.seek(0)
    return buffer.read()
