import io
import base64
import re
import logging
from datetime import datetime
from weasyprint import HTML

logger = logging.getLogger(__name__)

# ------------------------------
# Helper: strip HTML tags and markdown
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
    # Remove extra whitespace
    text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
    return text

# ------------------------------
# Generate PDF HTML (professional, with fallback)
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

    # Build the HTML template – minimal styling to avoid issues
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Retail Pulse Report</title>
        <style>
            body {{ font-family: sans-serif; margin: 40px; line-height: 1.5; }}
            h1, h2, h3 {{ color: #1e3c72; }}
            .kpi-grid {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 20px; margin: 20px 0; }}
            .kpi-card {{ background: #f0f4fa; padding: 15px; border-radius: 4px; text-align: center; }}
            .kpi-value {{ font-size: 24px; font-weight: bold; color: #1e3c72; }}
            .kpi-label {{ font-size: 12px; color: #4a5b7a; text-transform: uppercase; }}
            .filters {{ background: #eef2f9; padding: 10px; border-radius: 4px; margin: 20px 0; }}
            .insights {{ background: #f8fafc; padding: 20px; border-left: 4px solid #1e3c72; margin: 20px 0; }}
            .footer {{ margin-top: 40px; font-size: 11px; color: #7a8aa8; text-align: center; border-top: 1px solid #e9edf4; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <h1 style="text-align:center;">📊 Retail Pulse</h1>
        <h2 style="text-align:center; color:#2a5298;">Executive Business Report</h2>
        <p style="text-align:center;">{datetime.now().strftime('%B %d, %Y')}</p>
        <hr>

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

        <h2>AI‑Generated Insights</h2>
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
    Generate a PDF from HTML content with multiple fallback levels.
    """
    try:
        # First attempt: full HTML with all styling
        return HTML(string=html_content).write_pdf()
    except Exception as e:
        logger.warning(f"WeasyPrint with full HTML failed: {e}. Trying plain text fallback...")
        # Second attempt: strip all styling and use a minimal template
        try:
            # Extract insights from the HTML (roughly)
            # We'll try to extract the content inside the insights div, or fallback to plain text
            insights_match = re.search(r'<div class="insights">(.*?)</div>', html_content, re.DOTALL)
            if insights_match:
                insights_raw = insights_match.group(1)
            else:
                insights_raw = "No insights content available."

            # Convert to plain text (remove HTML tags)
            insights_text = strip_html_and_markdown(insights_raw)

            # Build a very simple HTML with no CSS
            simple_html = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>Report</title></head>
            <body>
                <h1>Retail Pulse Report</h1>
                <p>{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                <hr>
                <pre>{insights_text}</pre>
                <hr>
                <p><em>PDF generated in fallback mode due to rendering issues.</em></p>
            </body>
            </html>
            """
            return HTML(string=simple_html).write_pdf()
        except Exception as e2:
            logger.error(f"Plain text fallback also failed: {e2}")
            # Final fallback: return a PDF with an error message (using minimal HTML)
            error_html = f"""
            <!DOCTYPE html>
            <html><body>
            <h1>PDF Generation Failed</h1>
            <p>We encountered an error while generating the PDF. Please try again.</p>
            <pre>{e}</pre>
            </body></html>
            """
            return HTML(string=error_html).write_pdf()