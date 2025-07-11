from io import BytesIO
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from .models import BoxType

def generate_box_cheatsheet():
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title="Box Volume Cheat Sheet",
        author="Cargo Ghana"
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    
    # Content
    elements = []
    
    # Title
    title = Paragraph("Box Volume Cheat Sheet", title_style)
    elements.append(title)
    
    # Table headers
    headers = ['Box Type', 'Dimensions (cm)', 'Volume (m³)', 'Price per Box']
    data = [headers]
    
    # Add box types
    for box in BoxType.objects.all():
        dimensions = f"{box.length_cm} × {box.width_cm} × {box.height_cm}"
        volume = str(box.volume_m3.quantize(Decimal('0.001')))
        price = f"£{box.price_per_box}"
        data.append([box.name, dimensions, volume, price])
    
    # Create table
    table = Table(data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer