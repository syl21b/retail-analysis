import io
import base64
import re
from datetime import datetime
from weasyprint import HTML
import plotly.graph_objects as go
from plotly.io import to_image
import logging

logger = logging.getLogger(__name__)

# ------------------------------
# Helper: parse AI insights into sections
# ------------------------------
def parse_insights_sections(html_insights):
    """
    Extract sections from the AI insights HTML.
    Expects headings like ## Executive Summary, ## 1. Key Metrics, etc.
    Returns a dict: {section_title: content_text}
    """
    # Remove HTML tags to get plain text with markdown-like headings
    plain = re.sub(r'<[^>]+>', '', html_insights)
    lines = plain.split('\n')
    sections = {}
    current_title = "Introduction"
    current_content = []
    for line in lines:
        line = line.strip()
        if re.match(r'^##\s+', line):  # heading
            if current_content:
                sections[current_title] = '\n'.join(current_content).strip()
            current_title = re.sub(r'^##\s+', '', line).strip()
            current_content = []
        else:
            if line:
                current_content.append(line)
    if current_content:
        sections[current_title] = '\n'.join(current_content).strip()
    # If no sections were found, treat entire text as one section
    if not sections:
        sections["AI Insights"] = plain
    return sections

# ------------------------------
# Chart to base64 (with error handling)
# ------------------------------
def chart_to_base64(fig, width=800, height=400):
    try:
        img_bytes = to_image(fig, format='png', width=width, height=height)
        return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Chart to base64 error: {e}")
        return ""

# ------------------------------
# Generate PDF HTML (professional)
# ------------------------------
def generate_report_html(kpis, insights_html, charts, filters):
    # Generate chart images
    chart_imgs = {}
    chart_defs = [
        ('daily_revenue', 'Daily Revenue Trend', lambda: go.Figure(data=go.Scatter(
            x=charts['daily_revenue']['x'], y=charts['daily_revenue']['y'], mode='lines+markers'
        )).update_layout(title='Daily Revenue', xaxis_title='Date', yaxis_title='Revenue ($)')),
        ('category_revenue', 'Category Share', lambda: go.Figure(data=go.Pie(
            labels=charts['category_revenue']['labels'], values=charts['category_revenue']['values']
        )).update_layout(title='Revenue by Category')),
        ('monthly_revenue', 'Monthly Revenue', lambda: go.Figure(data=go.Bar(
            x=charts['monthly_revenue']['x'], y=charts['monthly_revenue']['y']
        )).update_layout(title='Monthly Revenue', xaxis_title='Month', yaxis_title='Revenue ($)')),
        ('city_revenue', 'Top Cities', lambda: go.Figure(data=go.Bar(
            x=charts['city_revenue']['labels'], y=charts['city_revenue']['values']
        )).update_layout(title='Revenue by City', xaxis_title='City', yaxis_title='Revenue ($)'))
    ]
    for key, title, fig_func in chart_defs:
        if key in charts and charts[key].get('x' if 'x' in charts[key] else 'labels'):
            try:
                fig = fig_func()
                chart_imgs[key] = chart_to_base64(fig)
            except Exception as e:
                logger.error(f"Failed to render {key}: {e}")

    # Ensure KPIs are numbers
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

    # Build HTML with professional styling
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Retail Pulse Report</title>
        <style>
            @page {{
                margin: 1.5cm;
                @bottom-center {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 10pt;
                    color: #7a8aa8;
                }}
            }}
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #1e2a44;
                line-height: 1.6;
            }}
            .cover {{
                text-align: center;
                padding: 100px 0 50px 0;
                page-break-after: always;
            }}
            .cover h1 {{
                font-size: 48pt;
                color: #1e3c72;
                margin: 0;
                letter-spacing: 2px;
            }}
            .cover .subtitle {{
                font-size: 24pt;
                color: #2a5298;
                margin: 20px 0 40px 0;
            }}
            .cover .date {{
                font-size: 16pt;
                color: #4a5b7a;
            }}
            .section-title {{
                color: #1e3c72;
                border-bottom: 2px solid #1e3c72;
                padding-bottom: 6px;
                margin-top: 30px;
            }}
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(4,1fr);
                gap: 20px;
                margin: 20px 0;
            }}
            .kpi-card {{
                background: #f0f4fa;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }}
            .kpi-value {{
                font-size: 26px;
                font-weight: 700;
                color: #1e3c72;
            }}
            .kpi-label {{
                font-size: 13px;
                color: #4a5b7a;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .filters {{
                background: #eef2f9;
                padding: 12px 16px;
                border-radius: 6px;
                margin: 20px 0;
                font-size: 14px;
            }}
            .chart-row {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin: 20px 0;
            }}
            .chart-box {{
                flex: 1 1 45%;
                min-width: 300px;
                background: #fff;
                padding: 10px;
                border: 1px solid #e9edf4;
                border-radius: 8px;
            }}
            .chart-box h3 {{
                margin: 0 0 10px 0;
                font-size: 16px;
                color: #2a5298;
            }}
            .chart-box img {{
                width: 100%;
                height: auto;
            }}
            .insights {{
                background: #f8fafc;
                padding: 20px;
                border-left: 4px solid #1e3c72;
                margin: 20px 0;
                border-radius: 0 6px 6px 0;
            }}
            .insights h2 {{
                color: #1e3c72;
                margin-top: 0;
            }}
            .insights h3 {{
                color: #2a5298;
                margin: 15px 0 5px 0;
            }}
            .insights ul, .insights ol {{
                padding-left: 20px;
            }}
            .footer {{
                margin-top: 40px;
                font-size: 11px;
                color: #7a8aa8;
                text-align: center;
                border-top: 1px solid #e9edf4;
                padding-top: 15px;
            }}
        </style>
    </head>
    <body>
        <!-- COVER PAGE -->
        <div class="cover">
            <h1>📊 Retail Pulse</h1>
            <div class="subtitle">Executive Business Report</div>
            <div class="date">{datetime.now().strftime('%B %d, %Y')}</div>
            <div style="margin-top: 50px; font-size: 14px; color: #4a5b7a;">
                <p>Prepared for the management team</p>
                <p>Data-driven insights for strategic decision making</p>
            </div>
        </div>

        <!-- BODY -->
        <h1>Executive Summary</h1>
        <div class="filters">
            <strong>Filters Applied:</strong> 
            Date {filters.get('dateRange',{}).get('min','any')} → {filters.get('dateRange',{}).get('max','any')}
            {f', City: {filters.get("selectedCity")}' if filters.get('selectedCity') else ''}
            {f', Category: {filters.get("selectedCategory")}' if filters.get('selectedCategory') else ''}
        </div>
        <div class="kpi-grid">
            <div class="kpi-card"><div class="kpi-value">${total_revenue:,.0f}</div><div class="kpi-label">Revenue</div></div>
            <div class="kpi-card"><div class="kpi-value">{total_orders:,.0f}</div><div class="kpi-label">Orders</div></div>
            <div class="kpi-card"><div class="kpi-value">{total_customers:,.0f}</div><div class="kpi-label">Customers</div></div>
            <div class="kpi-card"><div class="kpi-value">${avg_order_value:,.2f}</div><div class="kpi-label">AOV</div></div>
        </div>

        <h2 class="section-title">Visual Performance Overview</h2>
        <div class="chart-row">
            <div class="chart-box"><h3>Daily Revenue Trend</h3><img src="data:image/png;base64,{chart_imgs.get('daily_revenue','')}" /></div>
            <div class="chart-box"><h3>Category Share</h3><img src="data:image/png;base64,{chart_imgs.get('category_revenue','')}" /></div>
        </div>
        <div class="chart-row">
            <div class="chart-box"><h3>Monthly Revenue</h3><img src="data:image/png;base64,{chart_imgs.get('monthly_revenue','')}" /></div>
            <div class="chart-box"><h3>Top Cities</h3><img src="data:image/png;base64,{chart_imgs.get('city_revenue','')}" /></div>
        </div>

        <h2 class="section-title">AI‑Generated Insights</h2>
        <div class="insights">
            {insights_html}
        </div>

        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} · Confidential · For internal use only
        </div>
    </body>
    </html>
    """
    return html

def generate_pdf_from_html(html_content):
    return HTML(string=html_content).write_pdf()

# ------------------------------
# Generate PowerPoint (multi‑slide)
# ------------------------------
def generate_powerpoint_report(kpis, insights_html, charts, filters):
    prs = Presentation()

    # ----- Helper to add a text slide -----
    def add_text_slide(title, content, bullet=False):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = title
        tf = slide.placeholders[1].text_frame
        if bullet:
            lines = content.split('\n')
            for line in lines:
                p = tf.add_paragraph()
                p.text = line.strip()
                p.level = 0
            # Remove the first empty paragraph
            if tf.paragraphs[0].text == '':
                tf.paragraphs[0].text = ''
        else:
            tf.text = content

    # ----- Helper to add a chart slide -----
    def add_chart_slide(fig, title):
        try:
            img_bytes = to_image(fig, format='png', width=800, height=400)
            img_stream = io.BytesIO(img_bytes)
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            slide.shapes.add_picture(img_stream, Inches(1), Inches(1), width=Inches(8), height=Inches(4.5))
            # Add title
            title_box = slide.shapes.add_textbox(Inches(1), Inches(0.2), Inches(8), Inches(0.8))
            title_frame = title_box.text_frame
            title_frame.text = title
            title_frame.paragraphs[0].font.size = Pt(28)
            title_frame.paragraphs[0].font.bold = True
            title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        except Exception as e:
            logger.error(f"Failed to add chart slide '{title}': {e}")
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = f"Chart: {title}"
            tf = slide.placeholders[1].text_frame
            tf.text = "Chart could not be generated."

    # ----- 1. Title Slide -----
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    title_box = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(1.5))
    title_frame = title_box.text_frame
    title_frame.text = "Retail Pulse"
    title_frame.paragraphs[0].font.size = Pt(48)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    sub_box = slide.shapes.add_textbox(Inches(1), Inches(3), Inches(8), Inches(1))
    sub_frame = sub_box.text_frame
    sub_frame.text = "Executive Business Report"
    sub_frame.paragraphs[0].font.size = Pt(32)
    sub_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    date_box = slide.shapes.add_textbox(Inches(1), Inches(4.5), Inches(8), Inches(0.5))
    date_frame = date_box.text_frame
    date_frame.text = datetime.now().strftime("%B %d, %Y")
    date_frame.paragraphs[0].font.size = Pt(18)
    date_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    # ----- 2. Key Metrics (KPI) Slide -----
    total_revenue = kpis.get('total_revenue', 0)
    total_orders = kpis.get('total_orders', 0)
    total_customers = kpis.get('total_customers', 0)
    avg_order = kpis.get('avg_order_value', 0)
    kpi_text = f"""Revenue:          ${total_revenue:,.0f}
Orders:           {total_orders:,.0f}
Customers:        {total_customers:,.0f}
AOV:              ${avg_order:,.2f}
Filters:          Date {filters.get('dateRange',{}).get('min','any')} → {filters.get('dateRange',{}).get('max','any')}
{f'City: {filters.get("selectedCity")}' if filters.get('selectedCity') else ''}
{f'Category: {filters.get("selectedCategory")}' if filters.get('selectedCategory') else ''}"""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Key Metrics Overview"
    tf = slide.placeholders[1].text_frame
    tf.text = kpi_text

    # ----- 3. Charts (one per slide) -----
    if 'daily_revenue' in charts and charts['daily_revenue'].get('x'):
        fig = go.Figure(data=go.Scatter(x=charts['daily_revenue']['x'], y=charts['daily_revenue']['y'], mode='lines+markers'))
        fig.update_layout(title='Daily Revenue', xaxis_title='Date', yaxis_title='Revenue ($)')
        add_chart_slide(fig, 'Daily Revenue Trend')

    if 'category_revenue' in charts:
        fig = go.Figure(data=go.Pie(labels=charts['category_revenue']['labels'], values=charts['category_revenue']['values']))
        fig.update_layout(title='Revenue by Category')
        add_chart_slide(fig, 'Category Share')

    if 'monthly_revenue' in charts and charts['monthly_revenue'].get('x'):
        fig = go.Figure(data=go.Bar(x=charts['monthly_revenue']['x'], y=charts['monthly_revenue']['y']))
        fig.update_layout(title='Monthly Revenue', xaxis_title='Month', yaxis_title='Revenue ($)')
        add_chart_slide(fig, 'Monthly Revenue')

    if 'city_revenue' in charts:
        fig = go.Figure(data=go.Bar(x=charts['city_revenue']['labels'], y=charts['city_revenue']['values']))
        fig.update_layout(title='Revenue by City', xaxis_title='City', yaxis_title='Revenue ($)')
        add_chart_slide(fig, 'Top Cities')

    # ----- 4. AI Insights (split into sections) -----
    sections = parse_insights_sections(insights_html)
    # Define order of sections (optional)
    order = ["Executive Summary", "1. Key Metrics & Filters", "2. Deep Dive",
             "3. Root Causes", "4. Actionable Recommendations", "5. Expected Business Impact"]
    # Also include any other sections not in order
    remaining = [s for s in sections.keys() if s not in order]
    ordered_sections = order + remaining

    for sec in ordered_sections:
        if sec in sections and sections[sec].strip():
            content = sections[sec]
            # Determine if content is a list (contains numbered items or bullet points)
            lines = content.split('\n')
            # Remove empty lines
            lines = [l.strip() for l in lines if l.strip()]
            # Check if any line starts with a number or bullet
            is_bullet = any(re.match(r'^(\d+\.|\-|\*)', l) for l in lines)
            # Join lines
            text = '\n'.join(lines)
            # Limit text length to avoid overflow
            if len(text) > 2000:
                text = text[:2000] + "..."
            add_text_slide(sec, text, bullet=is_bullet)

    # ----- 5. Closing Slide -----
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    box = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(1.5))
    frame = box.text_frame
    frame.text = "Thank You"
    frame.paragraphs[0].font.size = Pt(54)
    frame.paragraphs[0].font.bold = True
    frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    sub_box = slide.shapes.add_textbox(Inches(1), Inches(4), Inches(8), Inches(0.8))
    sub_frame = sub_box.text_frame
    sub_frame.text = "Prepared by Retail Pulse Analytics"
    sub_frame.paragraphs[0].font.size = Pt(24)
    sub_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    return prs