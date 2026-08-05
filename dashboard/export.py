import io
import base64
import re
import logging
from datetime import datetime
from weasyprint import HTML
import plotly.graph_objects as go
from plotly.io import to_image

logger = logging.getLogger(__name__)

# ------------------------------
# Chart to base64 with robust fallback
# ------------------------------
def chart_to_base64(fig, width=800, height=400):
    """
    Render a Plotly figure to a base64 PNG.
    Returns empty string on any failure.
    """
    try:
        # Explicitly use kaleido engine
        img_bytes = to_image(fig, format='png', width=width, height=height, engine='kaleido')
        return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        logger.warning(f"Chart to base64 failed: {e}")
        return ""

# ------------------------------
# Generate PDF HTML (professional)
# ------------------------------
def generate_report_html(kpis, insights_html, charts, filters):
    # Generate chart images only if data exists
    chart_imgs = {}
    chart_defs = [
        ('daily_revenue', 'Daily Revenue Trend', lambda: go.Figure(data=go.Scatter(
            x=charts.get('daily_revenue', {}).get('x', []),
            y=charts.get('daily_revenue', {}).get('y', []),
            mode='lines+markers'
        )).update_layout(title='Daily Revenue', xaxis_title='Date', yaxis_title='Revenue ($)')),
        ('category_revenue', 'Category Share', lambda: go.Figure(data=go.Pie(
            labels=charts.get('category_revenue', {}).get('labels', []),
            values=charts.get('category_revenue', {}).get('values', [])
        )).update_layout(title='Revenue by Category')),
        ('monthly_revenue', 'Monthly Revenue', lambda: go.Figure(data=go.Bar(
            x=charts.get('monthly_revenue', {}).get('x', []),
            y=charts.get('monthly_revenue', {}).get('y', [])
        )).update_layout(title='Monthly Revenue', xaxis_title='Month', yaxis_title='Revenue ($)')),
        ('city_revenue', 'Top Cities', lambda: go.Figure(data=go.Bar(
            x=charts.get('city_revenue', {}).get('labels', []),
            y=charts.get('city_revenue', {}).get('values', [])
        )).update_layout(title='Revenue by City', xaxis_title='City', yaxis_title='Revenue ($)'))
    ]

    for key, title, fig_func in chart_defs:
        try:
            fig = fig_func()
            # Only generate if there is data
            if (fig.data and len(fig.data) > 0 and 
                ((hasattr(fig.data[0], 'x') and fig.data[0].x and len(fig.data[0].x) > 0) or
                 (hasattr(fig.data[0], 'labels') and fig.data[0].labels and len(fig.data[0].labels) > 0))):
                img_b64 = chart_to_base64(fig)
                chart_imgs[key] = img_b64 if img_b64 else ""
            else:
                chart_imgs[key] = ""
        except Exception as e:
            logger.error(f"Failed to render chart {key}: {e}")
            chart_imgs[key] = ""

    # Helper to format KPIs safely
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

    # Build the HTML template
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Retail Pulse Report</title>
        <style>
            @page {{ margin: 1.5cm; @bottom-center {{ content: "Page " counter(page) " of " counter(pages); font-size: 10pt; color: #7a8aa8; }} }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1e2a44; line-height: 1.6; }}
            .cover {{ text-align: center; padding: 100px 0 50px 0; page-break-after: always; }}
            .cover h1 {{ font-size: 48pt; color: #1e3c72; margin: 0; letter-spacing: 2px; }}
            .cover .subtitle {{ font-size: 24pt; color: #2a5298; margin: 20px 0 40px 0; }}
            .cover .date {{ font-size: 16pt; color: #4a5b7a; }}
            .section-title {{ color: #1e3c72; border-bottom: 2px solid #1e3c72; padding-bottom: 6px; margin-top: 30px; }}
            .kpi-grid {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 20px; margin: 20px 0; }}
            .kpi-card {{ background: #f0f4fa; padding: 15px; border-radius: 8px; text-align: center; }}
            .kpi-value {{ font-size: 26px; font-weight: 700; color: #1e3c72; }}
            .kpi-label {{ font-size: 13px; color: #4a5b7a; text-transform: uppercase; letter-spacing: 0.5px; }}
            .filters {{ background: #eef2f9; padding: 12px 16px; border-radius: 6px; margin: 20px 0; font-size: 14px; }}
            .chart-row {{ display: flex; flex-wrap: wrap; gap: 20px; margin: 20px 0; }}
            .chart-box {{ flex: 1 1 45%; min-width: 300px; background: #fff; padding: 10px; border: 1px solid #e9edf4; border-radius: 8px; }}
            .chart-box h3 {{ margin: 0 0 10px 0; font-size: 16px; color: #2a5298; }}
            .chart-box img {{ width: 100%; height: auto; }}
            .chart-box .no-chart {{ text-align: center; color: #7a8aa8; padding: 40px 0; font-size: 14px; }}
            .insights {{ background: #f8fafc; padding: 20px; border-left: 4px solid #1e3c72; margin: 20px 0; border-radius: 0 6px 6px 0; }}
            .insights h2 {{ color: #1e3c72; margin-top: 0; }}
            .insights h3 {{ color: #2a5298; margin: 15px 0 5px 0; }}
            .insights ul, .insights ol {{ padding-left: 20px; }}
            .footer {{ margin-top: 40px; font-size: 11px; color: #7a8aa8; text-align: center; border-top: 1px solid #e9edf4; padding-top: 15px; }}
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
            <div class="chart-box"><h3>Daily Revenue Trend</h3>{'<img src="data:image/png;base64,'+chart_imgs.get('daily_revenue','')+'" />' if chart_imgs.get('daily_revenue') else '<div class="no-chart">No data available</div>'}</div>
            <div class="chart-box"><h3>Category Share</h3>{'<img src="data:image/png;base64,'+chart_imgs.get('category_revenue','')+'" />' if chart_imgs.get('category_revenue') else '<div class="no-chart">No data available</div>'}</div>
        </div>
        <div class="chart-row">
            <div class="chart-box"><h3>Monthly Revenue</h3>{'<img src="data:image/png;base64,'+chart_imgs.get('monthly_revenue','')+'" />' if chart_imgs.get('monthly_revenue') else '<div class="no-chart">No data available</div>'}</div>
            <div class="chart-box"><h3>Top Cities</h3>{'<img src="data:image/png;base64,'+chart_imgs.get('city_revenue','')+'" />' if chart_imgs.get('city_revenue') else '<div class="no-chart">No data available</div>'}</div>
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
    """
    Generate a PDF from HTML content.
    If WeasyPrint fails, return a fallback PDF with an error message.
    """
    try:
        return HTML(string=html_content).write_pdf()
    except Exception as e:
        logger.error(f"WeasyPrint PDF generation failed: {e}")
        fallback_html = f"""
        <!DOCTYPE html>
        <html><body>
        <h1>PDF Generation Failed</h1>
        <p>We encountered an error while generating the PDF. Please try again.</p>
        <pre>{e}</pre>
        </body></html>
        """
        return HTML(string=fallback_html).write_pdf()