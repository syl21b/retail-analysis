import io
import re
import logging
from datetime import date
from typing import Any, Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

logger = logging.getLogger(__name__)

# Try to import html2text for markdown conversion
try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False
    logger.warning("html2text not installed. Falling back to basic HTML stripping.")

# ------------------------------
# Styling constants
# ------------------------------
INK = colors.HexColor("#102A43")
MUTED = colors.HexColor("#627D98")
NAVY = colors.HexColor("#163E63")
TEAL = colors.HexColor("#0D9488")
AMBER = colors.HexColor("#D97706")
RED = colors.HexColor("#C2410C")
PALE_BLUE = colors.HexColor("#EAF2F8")
PALE_TEAL = colors.HexColor("#E8F5F2")
PALE_AMBER = colors.HexColor("#FFF4E5")
RULE = colors.HexColor("#D9E2EC")
PAGE_W, PAGE_H = letter

# ------------------------------
# Safe formatting helpers
# ------------------------------
def money(value: Any, decimals: int = 0) -> str:
    try:
        return f"${float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "-"

def number(value: Any) -> str:
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "-"

def safe_text(value: Any) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))

# ------------------------------
# ReportLab styles
# ------------------------------
def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "eyebrow": ParagraphStyle("eyebrow", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8.5, leading=11, textColor=TEAL, spaceAfter=8, tracking=1.1),
        "cover_title": ParagraphStyle("cover_title", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=31, leading=35, textColor=INK, spaceAfter=10),
        "cover_subtitle": ParagraphStyle("cover_subtitle", parent=base["Normal"], fontSize=13,
            leading=19, textColor=MUTED),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=20, leading=25, textColor=INK, spaceBefore=0, spaceAfter=13),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=12.5, leading=16, textColor=NAVY, spaceBefore=13, spaceAfter=6),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontSize=9.6,
            leading=14.4, textColor=INK, spaceAfter=8),
        "small": ParagraphStyle("small", parent=base["Normal"], fontSize=8.3,
            leading=11.5, textColor=MUTED),
        "card_label": ParagraphStyle("card_label", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.5, leading=10, textColor=MUTED, tracking=.6),
        "card_value": ParagraphStyle("card_value", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=16.5, leading=20, textColor=INK),
        "callout": ParagraphStyle("callout", parent=base["Normal"], fontSize=10.2,
            leading=15, textColor=INK),
        "action": ParagraphStyle("action", parent=base["Normal"], fontSize=8.6,
            leading=11.6, textColor=INK),
    }

# ------------------------------
# Page drawing functions
# ------------------------------
def draw_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, 0, PAGE_W, 8, fill=1, stroke=0)
    canvas.restoreState()

def draw_page_chrome(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(.5)
    canvas.line(doc.leftMargin, PAGE_H - 40, PAGE_W - doc.rightMargin, PAGE_H - 40)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(NAVY)
    canvas.drawString(doc.leftMargin, PAGE_H - 31, "RETAIL PULSE")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(PAGE_W - doc.rightMargin, PAGE_H - 31, "CONFIDENTIAL | INTERNAL USE ONLY")
    canvas.setStrokeColor(RULE)
    canvas.line(doc.leftMargin, 38, PAGE_W - doc.rightMargin, 38)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 26, "Executive report")
    canvas.drawRightString(PAGE_W - doc.rightMargin, 26, f"{canvas.getPageNumber() - 1}")
    canvas.restoreState()

# ------------------------------
# Components
# ------------------------------
def metric_card(label: str, value: str, note: str, styles: dict[str, ParagraphStyle]) -> Table:
    card = Table([[Paragraph(label.upper(), styles["card_label"])],
                  [Paragraph(value, styles["card_value"])],
                  [Paragraph(note, styles["small"])]], colWidths=[1.58 * inch])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), .65, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 10), ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return card

def bullets(items: Iterable[str], styles: dict[str, ParagraphStyle]) -> list[Paragraph]:
    return [Paragraph(f'<font color="#0D9488">&#8226;</font> {safe_text(item)}', styles["body"])
            for item in items]

def section(title: str, content: list, styles: dict[str, ParagraphStyle]) -> list:
    return [Paragraph(title, styles["h2"]), *content, Spacer(1, 3)]

# ------------------------------
# Parser: convert AI insights HTML/markdown to structured dict
# ------------------------------
def parse_insights(insights_html: str, kpis: dict) -> dict:
    """Parse AI-generated HTML/markdown into structured fields."""
    # Convert HTML to markdown if possible
    if HAS_HTML2TEXT:
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0
        h.skip_internal_links = True
        markdown = h.handle(insights_html)
    else:
        # Strip HTML tags and keep text
        markdown = re.sub(r'<[^>]+>', '', insights_html)
        markdown = re.sub(r'\n\s*\n', '\n\n', markdown)

    # Clean up markdown artifacts
    markdown = re.sub(r'■', '', markdown)
    markdown = re.sub(r'(\d+)\\\.', r'\1.', markdown)
    markdown = re.sub(r'^---$', '', markdown, flags=re.MULTILINE)
    markdown = re.sub(r'^\s*#+\s+', '', markdown, flags=re.MULTILINE)

    lines = markdown.splitlines()
    clean_lines = [line.strip() for line in lines if line.strip()]
    text = '\n'.join(clean_lines)

    # Helper to extract section between two headings
    def extract_section(text: str, heading: str, next_heading_pattern: str = r'^#+\s+\d+\.') -> str:
        pattern = rf'##?\s+{re.escape(heading)}(.*?)(?=\n##?\s+\d+\.|\n##?\s+[A-Z]|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def extract_bullets(text: str) -> list[str]:
        """Extract bullet points (starting with - or * or •) from text."""
        bullets = []
        for line in text.splitlines():
            line = line.strip()
            if re.match(r'^[\*\-•]\s+(.+)', line):
                bullets.append(re.sub(r'^[\*\-•]\s+', '', line))
        return bullets

    # Extract sections
    summary = extract_section(text, "Executive Summary")
    if not summary:
        summary = extract_section(text, "Summary") or "Key insights summary not available."

    # Deep dive (section 2)
    deep_dive_text = extract_section(text, "Deep Dive")
    deep_dive_bullets = extract_bullets(deep_dive_text)
    if not deep_dive_bullets:
        # Fallback: treat each paragraph as a bullet
        deep_dive_bullets = [p for p in deep_dive_text.split('\n\n') if p.strip()]

    # Diagnosis (section 3)
    diagnosis = extract_section(text, "Root Causes") or extract_section(text, "Root causes")
    if not diagnosis:
        diagnosis = "Diagnosis not available."

    # Actions (section 4)
    actions_text = extract_section(text, "Actionable Recommendations")
    if not actions_text:
        actions_text = extract_section(text, "Recommendations")
    short_term_actions = []
    long_term_actions = []
    if actions_text:
        # Split by sub-headings "Short-term" and "Long-term"
        short_match = re.search(r'(Short-term|Short term)\s*\(.*?\)\s*(.*?)(?=(Long-term|Long term)|$)', actions_text, re.DOTALL | re.IGNORECASE)
        long_match = re.search(r'(Long-term|Long term)\s*\(.*?\)\s*(.*?)$', actions_text, re.DOTALL | re.IGNORECASE)
        if short_match:
            short_items = extract_bullets(short_match.group(2))
            short_term_actions = [('0-30 days', item, 'Track progress weekly') for item in short_items]
        if long_match:
            long_items = extract_bullets(long_match.group(2))
            long_term_actions = [('30-180 days', item, 'Track progress quarterly') for item in long_items]
        if not short_term_actions and not long_term_actions:
            # Fallback: extract all bullet points as actions
            all_actions = extract_bullets(actions_text)
            for i, action in enumerate(all_actions):
                if i < 3:
                    short_term_actions.append(('0-30 days', action, 'Track progress weekly'))
                else:
                    long_term_actions.append(('30-180 days', action, 'Track progress quarterly'))
    actions = short_term_actions + long_term_actions

    # Impact (section 5)
    impact_text = extract_section(text, "Expected Business Impact")
    impact_bullets = extract_bullets(impact_text) or ["Impact details not available."]

    # Generate signals from KPIs and key metrics
    signals = []
    repeat_rate = kpis.get('repeat_rate', None)
    if repeat_rate is not None:
        signals.append((f"{repeat_rate:.1f}% repeat rate", "Low repeat rate indicates customer loyalty challenges."))
    cancellation_rate = kpis.get('cancellation_rate', None)
    if cancellation_rate is not None:
        signals.append((f"{cancellation_rate:.1f}% cancellation rate", "High cancellation rate impacts revenue and trust."))
    at_risk_revenue = kpis.get('at_risk_revenue', None)
    if at_risk_revenue is not None:
        signals.append((f"${at_risk_revenue:,.0f} at risk", "High-value customers at risk of churn."))
    monthly_revenue_avg = kpis.get('monthly_revenue_avg', None)
    if monthly_revenue_avg is not None:
        signals.append((f"${monthly_revenue_avg:,.0f} monthly revenue", "Stable but plateaued revenue."))

    # If no signals from KPIs, use deep dive key points
    if not signals and deep_dive_bullets:
        for bullet in deep_dive_bullets[:3]:
            signals.append((bullet[:60] + "...", "Key insight from deep dive."))

    # Leadership questions (defaults)
    questions = [
        "Which two cancellation causes explain the largest share of failed orders?",
        "What share of first-time customers experience a cancellation or delayed-status event before they churn?",
        "Which retention offers create incremental profit rather than discounting customers who would have returned anyway?",
    ]

    return {
        "summary": summary,
        "signals": signals,
        "deep_dive": deep_dive_bullets,
        "diagnosis": diagnosis,
        "actions": actions,
        "impact": impact_bullets,
        "questions": questions,
    }

# ------------------------------
# Main PDF generator
# ------------------------------
def generate_executive_pdf(kpis: dict[str, Any], filters: dict[str, Any],
                           insights: dict[str, Any], generated_on: date | None = None) -> bytes:
    """Generate a polished executive PDF from structured data."""
    generated_on = generated_on or date.today()
    buffer = io.BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=letter, leftMargin=.72 * inch, rightMargin=.72 * inch,
                          topMargin=.72 * inch, bottomMargin=.62 * inch)
    cover_frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="cover")
    body_frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[cover_frame], onPage=draw_cover),
        PageTemplate(id="Body", frames=[body_frame], onPage=draw_page_chrome),
    ])
    s = make_styles()

    # Prepare filters scope
    date_range = filters.get("dateRange", {})
    scope = "All cities / all categories"
    if filters.get("selectedCity") or filters.get("selectedCategory"):
        scope = f"{filters.get('selectedCity') or 'All cities'} / {filters.get('selectedCategory') or 'All categories'}"

    story = [
        Spacer(1, 1.0 * inch),
        Paragraph("EXECUTIVE INTELLIGENCE", ParagraphStyle("cover_eyebrow", parent=s["eyebrow"], textColor=colors.HexColor("#5EEAD4"))),
        Paragraph("Retail Pulse", ParagraphStyle("cover_title_light", parent=s["cover_title"], textColor=colors.white)),
        Paragraph("Performance, retention, and operating priorities", ParagraphStyle("cover_subtitle_light", parent=s["cover_subtitle"], textColor=colors.HexColor("#D9E2EC"))),
        Spacer(1, .55 * inch),
        Table([[Paragraph("REPORTING PERIOD", s["card_label"]), Paragraph("SCOPE", s["card_label"])],
               [Paragraph(f"{safe_text(date_range.get('min', 'Not specified'))} to {safe_text(date_range.get('max', 'Not specified'))}", ParagraphStyle("cover_meta", parent=s["body"], textColor=colors.white)),
                Paragraph(safe_text(scope), ParagraphStyle("cover_meta2", parent=s["body"], textColor=colors.white))]],
              colWidths=[3 * inch, 3 * inch], style=TableStyle([
                  ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#214D75")),
                  ("LINEBELOW", (0, 0), (-1, 0), .5, colors.HexColor("#47779E")),
                  ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                  ("TOPPADDING", (0, 0), (-1, 0), 11), ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
              ])),
        Spacer(1, 2.25 * inch),
        Paragraph(f"Prepared {generated_on.strftime('%B %d, %Y')}", ParagraphStyle("cover_date", parent=s["small"], textColor=colors.HexColor("#D9E2EC"))),
        Paragraph("Confidential - for internal planning and decision-making", ParagraphStyle("cover_conf", parent=s["small"], textColor=colors.HexColor("#D9E2EC"))),
        NextPageTemplate("Body"), PageBreak(),
        Paragraph("Decision snapshot", s["h1"]),
        Paragraph(safe_text(insights.get("summary", "No summary available.")), s["callout"]),
        Spacer(1, 7),
    ]

    # KPI cards
    cards = [
        metric_card("Revenue", money(kpis.get("total_revenue")), "12-month performance", s),
        metric_card("Orders", number(kpis.get("total_orders")), "Completed and active demand", s),
        metric_card("Customers", number(kpis.get("total_customers")), "Customer base reached", s),
        metric_card("Avg. order value", money(kpis.get("avg_order_value"), 2), "Value per transaction", s),
    ]
    story += [Table([cards], colWidths=[1.58 * inch] * 4, hAlign="LEFT", style=TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ])), Spacer(1, 12)]

    # Signals
    signals = insights.get("signals", [])
    if signals:
        signal_rows = [[Paragraph("PRIORITY SIGNALS", s["card_label"]), Paragraph("WHY IT MATTERS", s["card_label"])]]
        for item, rationale in signals:
            signal_rows.append([Paragraph(safe_text(item), s["body"]), Paragraph(safe_text(rationale), s["body"])])
        signal_table = Table(signal_rows, colWidths=[2.25 * inch, 4.05 * inch], repeatRows=1)
        signal_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE_BLUE), ("LINEBELOW", (0, 0), (-1, 0), .6, RULE),
            ("LINEBELOW", (0, 1), (-1, -1), .35, RULE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story += [signal_table]

    # Deep dive
    deep_dive_bullets = insights.get("deep_dive", [])
    if deep_dive_bullets:
        story += section("What the data says", bullets(deep_dive_bullets, s), s)

    # Diagnosis
    diagnosis = insights.get("diagnosis", "")
    if diagnosis:
        story += section("Working diagnosis", [Paragraph(safe_text(diagnosis), s["body"])], s)

    # Action plan
    actions = insights.get("actions", [])
    if actions:
        story.append(Paragraph("Action plan", s["h1"]))
        story.append(Paragraph("Focus near-term effort on protecting high-value customers and repairing the order experience; use the next quarter to establish repeatable retention and fulfillment disciplines.", s["callout"]))
        action_rows = [[Paragraph("HORIZON", s["card_label"]), Paragraph("RECOMMENDED ACTION", s["card_label"]), Paragraph("MEASURE OF PROGRESS", s["card_label"])]]
        for horizon, action, measure in actions:
            action_rows.append([Paragraph(safe_text(horizon), s["body"]), Paragraph(safe_text(action), s["action"]), Paragraph(safe_text(measure), s["action"])])
        action_table = Table(action_rows, colWidths=[1.05 * inch, 3.55 * inch, 1.7 * inch], repeatRows=1)
        action_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE_TEAL), ("LINEBELOW", (0, 0), (-1, 0), .6, TEAL),
            ("LINEBELOW", (0, 1), (-1, -1), .35, RULE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story += [Spacer(1, 10), action_table]

    # Impact
    impact = insights.get("impact", [])
    if impact:
        story += section("Expected business impact", bullets(impact, s), s)

    # Leadership questions
    questions = insights.get("questions", [])
    if questions:
        story += section("Leadership questions for the next review", bullets(questions, s), s)

    doc.build(story)
    return buffer.getvalue()

# ------------------------------
# Entry point for Flask route
# ------------------------------
def generate_pdf_from_data(kpis: dict[str, Any], insights_html: str, filters: dict[str, Any]) -> bytes:
    """Generate PDF from raw data (used by the /api/export route)."""
    try:
        # Parse insights HTML into structured dict
        insights = parse_insights(insights_html, kpis)
        # Add extra KPIs from insights if needed
        # For signals, we might want to extract some from the parsed content
        return generate_executive_pdf(kpis, filters, insights)
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        # Fallback to a simple error PDF
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