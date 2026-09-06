import io
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)

def generate_qr_code_image(data):
    """Generates a QR Code image in PNG format as a BytesIO stream."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#0f172a', back_color='#ffffff')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def generate_pdf_ticket(payment_transaction):
    """
    Generates a professional PDF ticket for a successful PaymentTransaction.
    Returns bytes of the generated PDF document.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor('#0f172a')
    brand_color = colors.HexColor('#0284c7')
    card_bg = colors.HexColor('#f8fafc')
    border_color = colors.HexColor('#cbd5e1')

    title_style = ParagraphStyle(
        'TicketTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'TicketSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=brand_color,
        spaceAfter=10
    )

    label_style = ParagraphStyle(
        'TicketLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748b')
    )

    value_style = ParagraphStyle(
        'TicketValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=primary_color
    )

    story = []

    # Header Branding
    story.append(Paragraph('BOOKMYSEAT - OFFICIAL E-TICKET', title_style))
    story.append(Paragraph('Present this digital PDF ticket or QR code at theater entrance', subtitle_style))
    story.append(HRFlowable(width='100%', thickness=2, color=brand_color, spaceAfter=12))

    txn = payment_transaction
    movie = txn.movie
    theater = txn.theater
    user = txn.user

    # Generate Verification QR Code
    pay_id = txn.payment_id if txn.payment_id else 'VERIFIED'
    qr_data = f'BOOKMYSEAT_TICKET:{txn.order_id}|PAY:{pay_id}|SEATS:{txn.seats_summary}|USER:{user.username}'
    qr_buffer = generate_qr_code_image(qr_data)
    qr_img = Image(qr_buffer, width=1.4*inch, height=1.4*inch)

    loc = theater.location if theater.location else 'Main Auditorium'
    movie_info_html = f'<b>{movie.name}</b><br/><font color="#64748b" size="8">Duration: {movie.duration_formatted} | Cert: {movie.age_certification} | Rating: ⭐ {movie.rating}/10</font>'
    theater_info_html = f'<b>{theater.name}</b><br/><font color="#64748b" size="8">{loc}</font>'
    showtime_html = f'<b>{theater.time.strftime("%A, %d %b %Y at %I:%M %p")}</b>'

    user_name = user.get_full_name() or user.username
    user_email = user.email or 'N/A'

    ticket_data = [
        [
            Paragraph('<b>MOVIE DETAILS</b>', label_style),
            Paragraph('<b>THEATER & SCREEN</b>', label_style),
            Paragraph('<b>VERIFICATION QR</b>', label_style)
        ],
        [
            Paragraph(movie_info_html, value_style),
            Paragraph(theater_info_html, value_style),
            qr_img
        ],
        [
            Paragraph('<b>SHOW DATE & TIME</b>', label_style),
            Paragraph('<b>BOOKED SEATS</b>', label_style),
            Paragraph('<b>BOOKING REFERENCE</b>', label_style)
        ],
        [
            Paragraph(showtime_html, value_style),
            Paragraph(f'<font color="#0284c7" size="12"><b>{txn.seats_summary}</b></font>', value_style),
            Paragraph(f'Order: <b>{txn.order_id}</b><br/>Txn ID: <b>{pay_id}</b>', value_style)
        ],
        [
            Paragraph('<b>CUSTOMER NAME</b>', label_style),
            Paragraph('<b>AMOUNT PAID</b>', label_style),
            Paragraph('<b>PAYMENT STATUS</b>', label_style)
        ],
        [
            Paragraph(f'<b>{user_name}</b> ({user_email})', value_style),
            Paragraph(f'<b>₹{txn.amount:.2f} {txn.currency}</b>', value_style),
            Paragraph('<font color="#16a34a"><b>CONFIRMED / PAID</b></font>', value_style)
        ]
    ]

    ticket_table = Table(ticket_data, colWidths=[2.7*inch, 2.7*inch, 1.8*inch])
    ticket_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), card_bg),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('SPAN', (2,0), (2,1)),
    ]))
    story.append(ticket_table)
    story.append(Spacer(1, 14))

    footer_notes = (
        '<b>Important Terms & Instructions:</b><br/>'
        '1. Please arrive at the theater venue at least 15 minutes before the showtime.<br/>'
        '2. Show this E-Ticket with QR Code on your mobile phone at the auditorium entrance.<br/>'
        '3. Outside food and beverages may not be allowed inside the auditorium per theater policy.<br/>'
        '4. This ticket is non-transferable and non-refundable once confirmed.'
    )
    story.append(Paragraph(footer_notes, ParagraphStyle('FooterNotes', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor('#64748b'))))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
