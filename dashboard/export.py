import io
import re
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)

# Try to import html2text, fall back to regex stripping if not available
try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False
    logger.warning("html2text not installed. Falling back to basic HTML stripping.")

# ------------------------------
# Cleanup functions
# ------------------------------
def clean_markdown_text(text):
    """Remove unwanted characters and fix escape sequences."""
    # Remove raw Unicode bullet characters and other artifacts
    text = text.replace('■', '')
    text = text.replace('•', '•')  # ensure proper bullet
    # Remove escape sequences like 5\. -> 5.
    text = re.sub(r'(\d+)\\\.', r'\1.', text)
    # Remove standalone horizontal rules (---)
    text = re.sub(r'^\s*---\s*$', '', text, flags=re.MULTILINE)
    # Remove extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # collapse multiple blank lines
    # Remove non-breaking spaces and other weird chars
    text = text.replace('\xa0', ' ')
    return text.strip()

def format_inline(text):
    """Convert **bold** and *italic* to ReportLab-friendly tags."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Bold with __
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    # Italic with _
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
    return text

def strip_html_tags(text):
    """Remove HTML tags entirely."""
    return re.sub(r'<[^>]+>', '', text)

# ------------------------------
# Generate PDF with ReportLab
# ------------------------------
def generate_pdf_with_reportlab(kpis, insights_markdown, filters):
    """Generate a professional PDF report from markdown text."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()
    # Custom styles with a professional look
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'],
                                 fontSize=24, alignment=1, spaceAfter=12,
                                 textColor=colors.darkblue)
    heading1_style = ParagraphStyle('Heading1Style', parent=styles['Heading1'],
                                    fontSize=18, spaceAfter=6, spaceBefore=12,
                                    textColor=colors.darkblue)
    heading2_style = ParagraphStyle('Heading2Style', parent=styles['Heading2'],
                                    fontSize=16, spaceAfter=4, spaceBefore=8,
                                    textColor=colors.blue)
    heading3_style = ParagraphStyle('Heading3Style', parent=styles['Heading3'],
                                    fontSize=14, spaceAfter=4, spaceBefore=6,
                                    textColor=colors.blue)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'],
                                  fontSize=11, leading=14, spaceAfter=6)
    bullet_style = ParagraphStyle('BulletStyle', parent=normal_style,
                                  leftIndent=20, bulletIndent=0)
    number_style = ParagraphStyle('NumberStyle', parent=normal_style,
                                  leftIndent=20, bulletIndent=0)
    # Label style for sub-headings like "Positive Trends:"
    label_style = ParagraphStyle('LabelStyle', parent=normal_style,
                                 fontName='Helvetica-Bold',
                                 textColor=colors.darkblue)

    story = []

    # --- Cover Page ---
    story.append(Paragraph("📊 Retail Pulse – Executive Report", title_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", normal_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Confidential – For internal use only", normal_style))
    story.append(Spacer(1, 0.5 * inch))
    story.append(PageBreak())

    # --- Filters ---
    filter_text = "Filters Applied: "
    date_range = filters.get('dateRange', {})
    filter_text += f"Date {date_range.get('min','any')} → {date_range.get('max','any')}"
    if filters.get('selectedCity'):
        filter_text += f", City: {filters.get('selectedCity')}"
    if filters.get('selectedCategory'):
        filter_text += f", Category: {filters.get('selectedCategory')}"
    story.append(Paragraph(filter_text, normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # --- KPI Table ---
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

    # --- Visual Overview Placeholder ---
    story.append(Paragraph("Visual Overview", heading1_style))
    story.append(Paragraph("Interactive charts are available in the web dashboard. "
                           "This PDF report focuses on key metrics and AI-generated insights.", normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # --- AI Insights (parsed from markdown) ---
    story.append(Paragraph("AI‑Generated Insights", heading1_style))
    story.append(Spacer(1, 0.1 * inch))

    # Clean the markdown text
    clean_md = clean_markdown_text(insights_markdown)

    # Split into lines
    lines = clean_md.splitlines()
    i = 0
    in_list = False
    list_type = None  # 'bullet' or 'number'
    list_items = []

    def flush_list():
        nonlocal in_list, list_items, list_type
        if in_list and list_items:
            if list_type == 'bullet':
                for item in list_items:
                    story.append(Paragraph(f"• {format_inline(item)}", bullet_style))
            elif list_type == 'number':
                for idx, item in enumerate(list_items, 1):
                    story.append(Paragraph(f"{idx}. {format_inline(item)}", number_style))
            list_items = []
            in_list = False
            list_type = None

    while i < len(lines):
        line = lines[i].strip()
        # Skip empty lines (already handled in flush but keep for safety)
        if not line:
            flush_list()
            i += 1
            continue

        # Check for horizontal rule (already cleaned, but just in case)
        if re.match(r'^[-]{3,}$', line):
            flush_list()
            story.append(Spacer(1, 0.1 * inch))
            i += 1
            continue

        # Headings (detect lines starting with #)
        if line.startswith('## '):
            flush_list()
            content = line[3:].strip()
            # Remove any trailing colon or punctuation from heading
            content = re.sub(r'[:;]*$', '', content)
            story.append(Paragraph(format_inline(content), heading2_style))
            story.append(Spacer(1, 0.05 * inch))
            i += 1
            continue
        elif line.startswith('### '):
            flush_list()
            content = line[4:].strip()
            content = re.sub(r'[:;]*$', '', content)
            story.append(Paragraph(format_inline(content), heading3_style))
            story.append(Spacer(1, 0.05 * inch))
            i += 1
            continue
        elif line.startswith('# '):
            flush_list()
            content = line[2:].strip()
            content = re.sub(r'[:;]*$', '', content)
            story.append(Paragraph(format_inline(content), heading1_style))
            story.append(Spacer(1, 0.05 * inch))
            i += 1
            continue

        # Bullet lists: starts with - or *
        bullet_match = re.match(r'^[\*\-]\s+(.+)', line)
        # Numbered list: starts with digit and dot
        number_match = re.match(r'^(\d+)\.\s+(.+)', line)

        if bullet_match:
            if not in_list or list_type != 'bullet':
                flush_list()
                in_list = True
                list_type = 'bullet'
                list_items = []
            list_items.append(bullet_match.group(1))
            i += 1
            continue
        elif number_match:
            if not in_list or list_type != 'number':
                flush_list()
                in_list = True
                list_type = 'number'
                list_items = []
            list_items.append(number_match.group(2))
            i += 1
            continue

        # Plain paragraph (could be multi-line)
        # Collect lines until we hit an empty line or a heading/list marker
        para_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            # If next line is empty, heading, or list marker, break
            if (not next_line or
                next_line.startswith('#') or
                re.match(r'^[\*\-]\s+', next_line) or
                re.match(r'^(\d+)\.\s+', next_line)):
                break
            para_lines.append(next_line)
            i += 1

        # Join and format
        para_text = ' '.join(para_lines)
        # Check if it's a sub-heading like "Positive Trends:" or "Negative Trends:"
        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+:', para_text) or re.match(r'^[A-Z][a-z]+:', para_text):
            # Treat as a bold label
            story.append(Paragraph(format_inline(para_text), label_style))
        else:
            story.append(Paragraph(format_inline(para_text), normal_style))
        # Add a small spacer after paragraph
        story.append(Spacer(1, 0.05 * inch))

    # Flush any remaining list
    flush_list()

    # Footer
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Confidential – For internal use only", normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ------------------------------
# Main entry point for route
# ------------------------------
def generate_pdf_from_data(kpis, insights_html, filters):
    """Generate PDF from structured data."""
    try:
        # Convert HTML to markdown
        if HAS_HTML2TEXT:
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.body_width = 0  # no wrapping
            h.skip_internal_links = True
            markdown_text = h.handle(insights_html)
        else:
            # Fallback: strip HTML and try to infer structure
            text = strip_html_tags(insights_html)
            # Remove extra whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            markdown_text = '\n'.join(lines)
        return generate_pdf_with_reportlab(kpis, markdown_text, filters)
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