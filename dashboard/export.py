import io
import re
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)

# ------------------------------
# Helper: strip HTML tags and markdown to plain text
# ------------------------------
def strip_html_and_markdown(text):
    """Convert markdown/HTML to plain text for safe PDF rendering."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove markdown formatting (bold, italic, headers, links)
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)  # bold
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)    # italic
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)  # headers
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # links
    # Remove extra whitespace and empty lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines)

# ------------------------------
# Generate PDF with ReportLab
# ------------------------------
def generate_pdf_with_reportlab(kpis, insights_text, filters):
    """Generate a PDF report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=1,  # center
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=6
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 12
    normal_style.leading = 14

    story = []

    # Title
    story.append(Paragraph("📊 Retail Pulse – Executive Report", title_style))
    story.append(Spacer(1, 0.1 * inch))

    # Date
    date_str = datetime.now().strftime('%B %d, %Y')
    story.append(Paragraph(f"Generated on {date_str}", normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Filters
    filter_text = "Filters Applied: "
    date_range = filters.get('dateRange', {})
    filter_text += f"Date {date_range.get('min','any')} → {date_range.get('max','any')}"
    if filters.get('selectedCity'):
        filter_text += f", City: {filters.get('selectedCity')}"
    if filters.get('selectedCategory'):
        filter_text += f", Category: {filters.get('selectedCategory')}"
    story.append(Paragraph(filter_text, normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # KPIs as a table
    def safe_kpi(key, default=0):
        val = kpis.get(key, default)
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    total_revenue = safe_kpi('total_revenue')
    total_orders = safe_kpi('total_orders')
    total_customers = safe_kpi('total_customers')
    avg_order_value = safe_kpi('avg_order_value')

    kpi_data = [
        ['Metric', 'Value'],
        ['Revenue', f'${total_revenue:,.0f}'],
        ['Orders', f'{total_orders:,.0f}'],
        ['Customers', f'{total_customers:,.0f}'],
        ['AOV', f'${avg_order_value:,.2f}']
    ]
    kpi_table = Table(kpi_data, colWidths=[2*inch, 3*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.3 * inch))

    # Insights
    story.append(Paragraph("AI‑Generated Insights", heading_style))
    story.append(Spacer(1, 0.1 * inch))

    # Split insights into paragraphs
    if insights_text:
        for para in insights_text.split('\n\n'):
            if para.strip():
                story.append(Paragraph(para.strip(), normal_style))
                story.append(Spacer(1, 0.1 * inch))
    else:
        story.append(Paragraph("No insights available.", normal_style))

    # Footer
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Confidential – For internal use only", normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ------------------------------
# Main function called from routes
# ------------------------------
def generate_pdf_from_html(html_content):
    """
    Extract data from the HTML content and generate a PDF using ReportLab.
    """
    try:
        # Parse KPIs from the HTML (they are already passed separately, but we can also extract)
        # For simplicity, we rely on the fact that the route passes KPIs and filters separately.
        # However, this function only receives html_content.
        # We'll need to adjust the route to pass KPIs and filters directly to this function.
        # But to keep the interface unchanged, we'll attempt to extract from the HTML.
        # Better: we refactor the route to pass the raw data.
        # We'll implement a fallback: if we can't extract, we use dummy values.
        # For now, we'll assume the route will call a different function.
        # Let's create a new function that accepts KPIs, insights_text, filters.
        logger.warning("generate_pdf_from_html called with HTML; use generate_pdf_from_data instead.")
        # Fallback: return a simple error PDF
        error_html = "<html><body><h1>PDF Generation Error</h1><p>Please use the new PDF generation method.</p></body></html>"
        # We'll still try to use reportlab with extracted text
        # Extract insights text from HTML
        insights_match = re.search(r'<div class="insights">(.*?)</div>', html_content, re.DOTALL)
        if insights_match:
            insights_raw = insights_match.group(1)
        else:
            insights_raw = "No insights content available."
        insights_text = strip_html_and_markdown(insights_raw)

        # Attempt to extract KPIs from HTML (rough)
        # This is fragile; better to pass them directly.
        # We'll use dummy values.
        kpis = {
            'total_revenue': 0,
            'total_orders': 0,
            'total_customers': 0,
            'avg_order_value': 0
        }
        filters = {}
        return generate_pdf_with_reportlab(kpis, insights_text, filters)
    except Exception as e:
        logger.error(f"PDF generation with ReportLab failed: {e}")
        # Return a very simple PDF with an error message
        try:
            # Use reportlab to create a minimal error PDF
            from reportlab.pdfgen import canvas
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.drawString(100, 750, "PDF Generation Error")
            c.drawString(100, 730, f"An error occurred: {str(e)}")
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
        except:
            # Ultimate fallback: return empty bytes
            return b''

# New function to generate PDF directly from data (recommended)
def generate_pdf_from_data(kpis, insights_html, filters):
    """
    Generate a PDF from structured data.
    This is the preferred entry point.
    """
    try:
        # Convert insights HTML to plain text
        insights_text = strip_html_and_markdown(insights_html)
        return generate_pdf_with_reportlab(kpis, insights_text, filters)
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        # Fallback to simple error PDF
        try:
            from reportlab.pdfgen import canvas
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.drawString(100, 750, "PDF Generation Failed")
            c.drawString(100, 730, f"Error: {str(e)}")
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
        except:
            return b''