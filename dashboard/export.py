import io
import base64
import re
import logging
from datetime import datetime
from weasyprint import HTML

logger = logging.getLogger(__name__)

# ------------------------------
# Generate PDF HTML (professional) – without charts
# ------------------------------
def generate_report_html(kpis, insights_html, charts, filters):
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

    # Build the HTML template without chart images
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