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

# Try to import html2text for conversion
try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False
    logger.warning("html2text not installed. Falling back to basic HTML stripping.")


# ----------------------------------------------------------------------
# 1. Helper functions
# ----------------------------------------------------------------------

def clean_markdown(text):
    """Remove unwanted artifacts and fix formatting."""
    # Remove bullet characters
    text = text.replace('■', '')
    # Fix escaped dots: 5\. -> 5.
    text = re.sub(r'(\d+)\\\.', r'\1.', text)
    # Replace __Data Point:__ with **Data Point:**
    text = re.sub(r'__Data\s+Point:__', '**Data Point:**', text, flags=re.IGNORECASE)
    # Remove horizontal rules
    text = re.sub(r'^\s*---\s*$', '', text, flags=re.MULTILINE)
    # Collapse multiple blank lines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def format_inline(text):
    """Convert **bold** and *italic* to ReportLab tags."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
    return text


def strip_html_tags(text):
    """Remove HTML tags."""
    return re.sub(r'<[^>]+>', '', text)


# ----------------------------------------------------------------------
# 2. PDF generation with ReportLab
# ----------------------------------------------------------------------

def generate_pdf_with_reportlab(kpis, insights_markdown, filters):
    """Generate a professional PDF report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()

    # --- Custom styles ---
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
    label_style = ParagraphStyle('LabelStyle', parent=normal_style,
                                 fontName='Helvetica-Bold',
                                 textColor=colors.darkblue)
    sub_bullet_style = ParagraphStyle('SubBulletStyle', parent=bullet_style,
                                      leftIndent=40, bulletIndent=0)

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

    # --- KPI Cards (2×2 grid) ---
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
        ['Revenue', f'${total_revenue:,.0f}'],
        ['Orders', f'{total_orders:,.0f}'],
        ['Customers', f'{total_customers:,.0f}'],
        ['AOV', f'${avg_order_value:,.2f}']
    ]

    kpi_table = Table(kpi_data, colWidths=[2.5*inch, 2.5*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.beige),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 14),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (0,-1), 16),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.darkblue),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.3 * inch))

    # --- AI Insights (structured parsing) ---
    story.append(Paragraph("AI‑Generated Insights", heading1_style))
    story.append(Spacer(1, 0.1 * inch))

    # Clean and preprocess markdown
    clean_md = clean_markdown(insights_markdown)
    clean_md = re.sub(r'^#+\s+', '', clean_md, flags=re.MULTILINE)

    lines = clean_md.splitlines()
    i = 0
    in_list = False
    list_type = None
    list_items = []
    list_indent = 0

    def flush_list():
        nonlocal in_list, list_items, list_type, list_indent
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
            list_indent = 0

    def get_heading_level(line):
        """Detect if line is a major section (2) or sub‑section (3)."""
        if re.match(r'^\d+\.\s+[A-Z]', line):
            return 2
        if re.match(r'^(Short-term|Long-term)\s*\(', line, re.IGNORECASE):
            return 3
        return 0

    # Process line by line
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            flush_list()
            i += 1
            continue

        # ---- 1. Headings ----
        h_level = get_heading_level(line)
        if h_level:
            flush_list()
            if h_level == 2:
                # FIX: keep the full line including the number prefix
                content = line  # was: re.sub(r'^\d+\.\s+', '', line)
                story.append(Paragraph(format_inline(content), heading2_style))
            else:
                story.append(Paragraph(format_inline(line), heading3_style))
            story.append(Spacer(1, 0.05 * inch))
            i += 1
            continue

        # ---- 2. Sub‑headings (e.g., "Revenue Performance:") ----
        if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+:', line) or re.match(r'^[A-Z][a-z]+:', line):
            flush_list()
            story.append(Paragraph(format_inline(line), label_style))
            i += 1
            continue

        # ---- 3. Bullet lists ----
        bullet_match = re.match(r'^[\*\-]\s+(.+)', line)
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

        # ---- 4. "Data Point:" lines (bold label) ----
        if re.match(r'^\*\*Data\s+Point:\*\*', line, re.IGNORECASE) or re.match(r'^__Data\s+Point:__', line, re.IGNORECASE):
            content = re.sub(r'^\*\*Data\s+Point:\*\*\s*', '', line, flags=re.IGNORECASE)
            content = re.sub(r'^__Data\s+Point:__\s*', '', content, flags=re.IGNORECASE)
            if list_items:
                list_items.append(f"  - **Data Point:** {content}")
            else:
                story.append(Paragraph(f"<b>Data Point:</b> {format_inline(content)}", normal_style))
            i += 1
            continue

        # ---- 5. Regular paragraphs (may span multiple lines) ----
        para_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if (not next_line or
                get_heading_level(next_line) or
                re.match(r'^[\*\-]\s+', next_line) or
                re.match(r'^(\d+)\.\s+', next_line) or
                re.match(r'^\*\*Data\s+Point:\*\*', next_line, re.IGNORECASE) or
                re.match(r'^__Data\s+Point:__', next_line, re.IGNORECASE) or
                re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+:', next_line) or
                re.match(r'^[A-Z][a-z]+:', next_line)):
                break
            para_lines.append(next_line)
            i += 1

        para_text = ' '.join(para_lines)
        story.append(Paragraph(format_inline(para_text), normal_style))
        story.append(Spacer(1, 0.05 * inch))

    flush_list()

    # --- Footer ---
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Confidential – For internal use only", normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ----------------------------------------------------------------------
# 3. Entry point for route
# ----------------------------------------------------------------------

def generate_pdf_from_data(kpis, insights_html, filters):
    """Convert HTML insights to markdown and generate PDF."""
    try:
        if HAS_HTML2TEXT:
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.body_width = 0
            h.skip_internal_links = True
            markdown_text = h.handle(insights_html)
        else:
            # Fallback: strip tags and keep plain text
            text = strip_html_tags(insights_html)
            # Remove extra whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            markdown_text = '\n'.join(lines)
        return generate_pdf_with_reportlab(kpis, markdown_text, filters)
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        # Ultimate fallback: a simple error PDF
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