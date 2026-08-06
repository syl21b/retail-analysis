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

# ------------------------------
# Convert markdown/HTML to plain text for fallback
# ------------------------------
def strip_html_and_markdown(text):
    """Remove HTML and markdown, return plain text."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines)

# ------------------------------
# Lightweight markdown to ReportLab-friendly HTML
# ------------------------------
def markdown_to_rl_html(text):
    """Convert markdown subset to HTML for ReportLab Paragraph."""
    # Escape ampersands and angle brackets (but we will use <b>, etc.)
    # Replace **bold** with <b>bold</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Replace *italic* with <i>italic</i>
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Replace __bold__ with <b>bold</b>
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    # Replace _italic_ with <i>italic</i>
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
    # Handle line breaks: replace \n with <br/> (but we'll handle at paragraph level)
    return text

# ------------------------------
# Generate PDF with ReportLab
# ------------------------------
def generate_pdf_with_reportlab(kpis, insights_text, filters):
    """Generate a professional PDF report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()
    # Custom styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'],
                                 fontSize=24, alignment=1, spaceAfter=12)
    heading1_style = ParagraphStyle('Heading1Style', parent=styles['Heading1'],
                                    fontSize=18, spaceAfter=6, spaceBefore=12)
    heading2_style = ParagraphStyle('Heading2Style', parent=styles['Heading2'],
                                    fontSize=16, spaceAfter=4, spaceBefore=8)
    heading3_style = ParagraphStyle('Heading3Style', parent=styles['Heading3'],
                                    fontSize=14, spaceAfter=4, spaceBefore=6)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'],
                                  fontSize=11, leading=14, spaceAfter=6)
    bullet_style = ParagraphStyle('BulletStyle', parent=normal_style,
                                  leftIndent=20, bulletIndent=0)
    number_style = ParagraphStyle('NumberStyle', parent=normal_style,
                                  leftIndent=20, bulletIndent=0)

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

    # Process insights text line by line
    lines = insights_text.splitlines()
    i = 0
    in_list = False
    list_type = None  # 'bullet' or 'number'
    list_items = []

    def flush_list():
        nonlocal in_list, list_items, list_type
        if in_list and list_items:
            if list_type == 'bullet':
                for item in list_items:
                    story.append(Paragraph(f"• {item}", bullet_style))
            elif list_type == 'number':
                for idx, item in enumerate(list_items, 1):
                    story.append(Paragraph(f"{idx}. {item}", number_style))
            list_items = []
            in_list = False
            list_type = None

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            flush_list()
            i += 1
            continue

        # Detect headings
        if line.startswith('## '):
            flush_list()
            content = line[3:].strip()
            story.append(Paragraph(markdown_to_rl_html(content), heading2_style))
            i += 1
            continue
        elif line.startswith('### '):
            flush_list()
            content = line[4:].strip()
            story.append(Paragraph(markdown_to_rl_html(content), heading3_style))
            i += 1
            continue
        elif line.startswith('# '):
            flush_list()
            content = line[2:].strip()
            story.append(Paragraph(markdown_to_rl_html(content), heading1_style))
            i += 1
            continue

        # Detect bullets and numbered lists
        bullet_match = re.match(r'^[\*\-]\s+(.+)', line)
        number_match = re.match(r'^(\d+)\.\s+(.+)', line)
        if bullet_match:
            if not in_list or list_type != 'bullet':
                flush_list()
                in_list = True
                list_type = 'bullet'
                list_items = []
            list_items.append(markdown_to_rl_html(bullet_match.group(1)))
            i += 1
            continue
        elif number_match:
            if not in_list or list_type != 'number':
                flush_list()
                in_list = True
                list_type = 'number'
                list_items = []
            list_items.append(markdown_to_rl_html(number_match.group(2)))
            i += 1
            continue

        # Regular paragraph
        flush_list()
        # Handle bold/italic in paragraph
        story.append(Paragraph(markdown_to_rl_html(line), normal_style))
        i += 1

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
    """Generate PDF from structured data (preferred)."""
    try:
        # Convert insights HTML to plain text (markdown-ish) but we'll keep markdown formatting
        # Actually we want to keep markdown, so we don't strip markdown here.
        # We'll pass insights_html directly as a string containing markdown (not HTML).
        # But insights_html contains HTML generated by renderMarkdown in the frontend.
        # We need to convert HTML to markdown or plain text with structure.
        # However, the insights_html from frontend is already HTML with <h1>, <h2>, <ul>, <li>.
        # Since we have markdown-like content originally, we could keep it as markdown.
        # For simplicity, we'll extract the text content and then parse as markdown.
        # But we lost the markdown. Let's instead parse the HTML to extract structure.
        # Better: in the frontend, we already have the raw markdown before conversion.
        # We could send the raw markdown as well, but we don't.
        # For now, we'll use the plain text version but we'll try to preserve headings by looking for patterns.
        # Let's convert HTML to plain text but keep heading markers.
        # This is a temporary workaround.
        # In a real solution, you would pass the raw markdown from the backend.
        # Since we don't have that, we'll extract headings from HTML.
        # We'll use regex to find <h1>, <h2>, etc. and convert to markdown.
        # We'll then parse the markdown as before.
        import html2text
        # Convert HTML to markdown using html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        markdown_text = h.handle(insights_html)
        # Now markdown_text contains markdown
        # But html2text may not be installed. Let's add it.
        # Alternatively, we can just use plain text without structure as fallback.
        # For now, we'll use the existing strip function and then parse.
        # We'll try to detect headings in the plain text.
        # Let's just use the stripped text and then split by "## " etc.
        # Actually we can use the original insights_text which was generated as markdown.
        # But we don't have it. We only have the HTML version.
        # We'll send the raw markdown from the backend to the frontend, and the frontend sends it back for PDF.
        # That's the proper fix.
        # For now, we'll work with what we have: insights_html is HTML.
        # We'll convert it to markdown using html2text (if available) else fallback to plain text.
        try:
            import html2text
            h = html2text.HTML2Text()
            h.ignore_links = False
            markdown_text = h.handle(insights_html)
        except ImportError:
            # fallback: strip tags and hope for the best
            markdown_text = strip_html_and_markdown(insights_html)
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