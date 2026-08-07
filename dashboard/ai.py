import logging
import concurrent.futures
import re
from datetime import datetime
from .config import Config
from .data_loader import friendly_data
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# ------------------------------
#  Multi-Provider AI Setup
# ------------------------------
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not installed. Gemini disabled.")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("groq not installed. Groq disabled.")

genai_client = None
groq_client = None

if Config.GEMINI_API_KEY and GENAI_AVAILABLE:
    genai_client = genai.Client(api_key=Config.GEMINI_API_KEY)
    logger.info("✅ Gemini AI ready.")
if Config.GROQ_API_KEY and GROQ_AVAILABLE:
    try:
        groq_client = Groq(api_key=Config.GROQ_API_KEY)
        logger.info("✅ Groq AI ready.")
    except Exception as e:
        logger.error(f"Failed to initialise Groq client: {e}")
        groq_client = None

def call_ai_provider(prompt, timeout=30):
    if genai_client:
        try:
            response = genai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=8192,   # increased to avoid truncation
                    top_p=0.95
                )
            )
            logger.info("✅ AI response from Gemini.")
            return response.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
    if groq_client:
        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4096,   # increased for Groq
                top_p=0.95,
                timeout=timeout
            )
            logger.info("✅ AI response from Groq.")
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq error: {e}")
    logger.warning("No AI provider available.")
    return None

def call_ai_provider_with_timeout(prompt, timeout=30):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(call_ai_provider, prompt, timeout)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        logger.error(f"AI call timed out after {timeout}s")
        executor.shutdown(wait=False)
        return None
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        executor.shutdown(wait=False)
        return None

# ------------------------------
#  AI Persona Templates (unchanged)
# ------------------------------
PERSONA_TEMPLATES = {
    "conservative_cfo": """
You are a **Conservative CFO** with 20+ years of experience in financial risk management and cost control.  
Your primary concern is protecting the company's bottom line, ensuring operational efficiency, and mitigating financial risks.  
You are cautious, data-driven, and skeptical of bold investments without clear ROI.  
Your language is formal, precise, and numbers-focused.

When analyzing the data, you must:
- Highlight any revenue declines, margin erosion, or unexpected costs.
- Emphasize cost-saving opportunities and efficiency gains.
- Warn against aggressive spending or expansion without solid returns.
- Recommend conservative strategies such as cost reduction, debt management, and cash preservation.

Write a concise, actionable business report with these sections:
## Executive Summary (2-3 sentences)
## 1. Key Metrics & Filters
## 2. Deep Dive (Revenue, Retention, Operations)
## 3. Root Causes (from a financial risk perspective)
## 4. Actionable Recommendations (Short-term, Long-term) - focus on cost control and risk mitigation
## 5. Expected Business Impact - quantify savings or risk reduction

Make sure to cover ALL sections. Do not truncate your response.
""",
    "growth_cmo": """
You are an **Aggressive Growth CMO** with a track record of scaling businesses through innovative marketing and customer acquisition.  
You are optimistic, forward-looking, and prioritize top-line revenue growth, market share, and brand awareness.  
You love bold moves, experimentation, and rapid iteration.

When analyzing the data, you must:
- Focus on revenue growth opportunities, untapped markets, and customer expansion.
- Highlight high-potential segments, product lines, or geographies.
- Recommend aggressive marketing campaigns, partnerships, and customer retention programs.
- Be enthusiastic about new initiatives, even if they involve some risk.

Write a concise, actionable business report with these sections:
## Executive Summary (2-3 sentences)
## 1. Key Metrics & Filters
## 2. Deep Dive (Revenue, Retention, Operations)
## 3. Root Causes (from a growth and acquisition perspective)
## 4. Actionable Recommendations (Short-term, Long-term) - focus on scaling, acquisition, and loyalty
## 5. Expected Business Impact - project revenue uplift and market share gains

Make sure to cover ALL sections. Do not truncate your response.
""",
    "balanced_analyst": """
You are a **Balanced Business Analyst** who weighs both risks and opportunities objectively.  
You are pragmatic, data-driven, and strive to provide a 360-degree view of the business.  
You avoid extremes and favor evidence-based, sustainable strategies.

When analyzing the data, you must:
- Present both positive and negative trends equally.
- Provide a neutral assessment of revenue, retention, and operational performance.
- Recommend balanced actions that consider cost, growth, and customer satisfaction.
- Support all recommendations with clear data points.

Write a concise, actionable business report with these sections:
## Executive Summary (2-3 sentences)
## 1. Key Metrics & Filters
## 2. Deep Dive (Revenue, Retention, Operations)
## 3. Root Causes (balanced perspective)
## 4. Actionable Recommendations (Short-term, Long-term) - pragmatic and data-backed
## 5. Expected Business Impact - realistic outcomes

Make sure to cover ALL sections. Do not truncate your response.
"""
}

feedback_store = {
    "conservative_cfo": {"up": 0, "down": 0},
    "growth_cmo": {"up": 0, "down": 0},
    "balanced_analyst": {"up": 0, "down": 0}
}

# ---------- Cached extra metrics ----------
extra_metrics_cache = TTLCache(maxsize=10, ttl=300)

def get_cached_extra_metrics():
    if 'extra_metrics' not in extra_metrics_cache:
        extra_metrics_cache['extra_metrics'] = _get_additional_metrics()
    return extra_metrics_cache['extra_metrics']

def _get_additional_metrics():
    """Load only tiny summary datasets."""
    extra = {}
    try:
        status = friendly_data.get('Order Status Distribution')
        if status is not None and not status.empty:
            extra['order_status'] = status.to_dict('records')
        else:
            extra['order_status'] = []

        pay = friendly_data.get('Payment Method Analysis')
        if pay is not None and not pay.empty:
            extra['top_payment_method'] = pay.iloc[0].get('payment_method', 'N/A')
        else:
            extra['top_payment_method'] = 'N/A'

        churn = friendly_data.get('Churn Detection')
        if churn is not None and 'churn_rate' in churn.columns:
            extra['churn_rate'] = churn['churn_rate'].iloc[0]
        else:
            extra['churn_rate'] = None

        subcat = friendly_data.get('Revenue by Product SubCategory')
        if subcat is not None and not subcat.empty:
            possible_cols = ['subcategory', 'product_subcategory', 'sub_category', 'product_category']
            subcat_field = None
            for col in possible_cols:
                if col in subcat.columns:
                    subcat_field = col
                    break
            if subcat_field:
                extra['top_subcategories'] = subcat.head(3)[subcat_field].tolist()
            else:
                extra['top_subcategories'] = subcat.head(3).iloc[:, 0].tolist()
        else:
            extra['top_subcategories'] = []

        cohort = friendly_data.get('Cohort Retention Analysis')
        if cohort is not None and not cohort.empty:
            extra['cohort_sample'] = cohort.head(3).to_dict('records')
        else:
            extra['cohort_sample'] = []

        extra['rfm_full'] = []

    except Exception as e:
        logger.warning(f"Could not fetch extra metrics: {e}")
    return extra

# ------------------------------
#  Helper: status summary from DataFrame or list
# ------------------------------
def get_status_summary(status_data):
    """
    Return a human-readable summary of order status distribution.
    Accepts either a DataFrame or a list of dicts (as returned by to_dict('records')).
    """
    if status_data is None:
        return "No order status data available"

    if isinstance(status_data, list):
        if not status_data:
            return "No order status data available"
        total_orders = sum(row.get('order_count', 0) for row in status_data)
        if total_orders == 0:
            return "No order status data available"
        status_list = []
        for row in status_data:
            status = row.get('order_status', 'unknown')
            count = row.get('order_count', 0)
            pct = (count / total_orders * 100) if total_orders else 0
            status_list.append(f"{status}: {count} ({pct:.1f}%)")
        return ", ".join(status_list[:5])

    if hasattr(status_data, 'empty') and status_data.empty:
        return "No order status data available"
    total_orders = status_data['order_count'].sum() if 'order_count' in status_data else 0
    if total_orders == 0:
        return "No order status data available"
    status_list = []
    for _, row in status_data.iterrows():
        status = row.get('order_status', 'unknown')
        count = row.get('order_count', 0)
        pct = (count / total_orders * 100) if total_orders else 0
        status_list.append(f"{status}: {count} ({pct:.1f}%)")
    return ", ".join(status_list[:5])

def fix_list_numbering(text):
    pattern = r'(## 5\. Expected Business Impact.*?)(?=\n## |\n---|\Z)'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return text
    section = match.group(1)
    lines = section.split('\n')
    new_lines = []
    counter = 1
    for line in lines:
        if re.match(r'^\s*1\.\s+', line):
            new_line = re.sub(r'^\s*1\.\s+', f'{counter}. ', line)
            new_lines.append(new_line)
            counter += 1
        else:
            new_lines.append(line)
    fixed_section = '\n'.join(new_lines)
    return text.replace(section, fixed_section)

def generate_local_deep_insights_fallback(kpis, filters, daily_revenue, monthly_revenue, top_cities,
                                          revenue_categories, repeat_customers, clv_data, rfm_segments,
                                          cohort_retention, anomalies, high_risk, extra_metrics):
    one_time = 0
    repeat_cust = 0
    one_time = repeat_customers.get('one-time', repeat_customers.get('one_time', 0))
    repeat_cust = repeat_customers.get('repeat', repeat_customers.get('repeat_customer', 0))
    if one_time == 0:
        for k, v in repeat_customers.items():
            if 'one' in str(k).lower() and 'time' in str(k).lower():
                one_time = v
                break
    if repeat_cust == 0:
        for k, v in repeat_customers.items():
            if 'repeat' in str(k).lower():
                repeat_cust = v
                break
    total_cust = one_time + repeat_cust
    repeat_rate = (repeat_cust / total_cust * 100) if total_cust else 0

    def to_float(val, default=0.0):
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    aov = to_float(kpis.get('avg_order_value', 0))
    total_rev = to_float(kpis.get('total_revenue', 0))
    total_orders = int(kpis.get('total_orders', 0))

    status_summary = get_status_summary(extra_metrics.get('order_status'))
    top_payment = extra_metrics.get('top_payment_method', 'N/A')

    report = []
    report.append("# 📊 Retail Analytics - Deep Business Report (AI Fallback)\n")
    report.append("## Executive Summary\n")
    if repeat_rate < 30:
        report.append(f"⚠️ **Critical**: Only {repeat_rate:.1f}% repeat buyers. Retention is a major risk.\n")
    else:
        report.append(f"✅ **Healthy loyalty**: {repeat_rate:.1f}% repeat rate.\n")
    if anomalies:
        report.append(f"📉 **{len(anomalies)} revenue anomaly days** (>20% drop).\n")
    if high_risk:
        report.append(f"💎 **{len(high_risk)} high-value customers at risk** of churn.\n")
    report.append(f"Overall: ${total_rev:,.0f} revenue from {total_orders:,} orders, AOV ${aov:,.0f}.\n")
    report.append("## 1. Key Metrics & Filters\n")
    date_filter = filters.get('dateRange', {})
    report.append(f"- **Filters**: Date {date_filter.get('min','any')} → {date_filter.get('max','any')}, City {filters.get('selectedCity','any')}, Category {filters.get('selectedCategory','any')}\n")
    report.append(f"- **AOV**: ${aov:,.0f} - " + ("low, consider bundling." if aov < 50 else "healthy.") + "\n")
    report.append(f"- **Repeat Rate**: {repeat_rate:.1f}% - " + ("needs immediate action." if repeat_rate < 30 else "good, aim for 40%+.") + "\n")
    report.append("## 2. Deep Dive\n")
    report.append("### Revenue & Growth\n")
    if top_cities:
        report.append(f"- Top city: {top_cities[0].get('city', 'N/A')}. ")
    if revenue_categories:
        report.append(f"Top category: {revenue_categories[0].get('category', 'N/A')}.\n")
    if anomalies:
        report.append(f"- Anomaly days: {', '.join([a.get('date','')[:10] for a in anomalies[:3]])}.\n")
    report.append("\n### Retention & Loyalty\n")
    report.append(f"- Repeat rate {repeat_rate:.1f}% is " + ("below benchmark." if repeat_rate < 30 else "acceptable.") + "\n")
    if clv_data.get('highest'):
        avg_top_clv = sum(to_float(c.get('total_net_amount', c.get('total_revenue', 0))) for c in clv_data['highest']) / max(len(clv_data['highest']), 1)
        report.append(f"- Top 5 CLV: ${avg_top_clv:,.0f} avg.\n")
    if high_risk:
        high_risk_total = sum(to_float(c.get('monetary', 0)) for c in high_risk)
        report.append(f"- High-risk VIPs: {len(high_risk)} customers, total ${high_risk_total:,.0f} at stake.\n")
    report.append("\n### Operations & Risk\n")
    report.append(f"- Order Status Distribution: {status_summary}\n")
    report.append(f"- Top payment method: {top_payment}.\n")
    report.append("\n## 3. Root Causes\n")
    if repeat_rate < 30:
        report.append("- Low repeat rate → weak post-purchase engagement, no loyalty program.\n")
    if anomalies:
        report.append("- Revenue drops → ended promotions, stockouts, or technical issues.\n")
    if high_risk:
        report.append("- High-value churn risk → lack of VIP treatment or relevant offers.\n")
    report.append("\n## 4. Actionable Recommendations\n")
    report.append("### Short-Term (30 days)\n")
    if repeat_rate < 30:
        report.append("1. Launch win-back email with 15% off for one-time buyers.\n")
    if aov < 75:
        report.append("2. Create product bundles to increase AOV by 20%.\n")
    if anomalies:
        report.append("3. Set up daily revenue anomaly alerts (Slack/email).\n")
    if high_risk:
        report.append(f"4. Personalised VIP discount codes to top {min(5, len(high_risk))} at-risk customers.\n")
    if not any([repeat_rate < 30, aov < 75, anomalies, high_risk]):
        report.append("1. Run A/B test on checkout page.\n")
        report.append("2. Introduce referral program.\n")
    report.append("\n### Long-Term (6-12 months)\n")
    report.append("- Tiered loyalty program to raise repeat rate to 45%.\n")
    report.append("- Predictive churn model for automated re-engagement.\n")
    if top_cities:
        report.append(f"- Expand product assortment in {top_cities[0].get('city', 'top city')}.\n")
    report.append("\n## 5. Expected Business Impact\n")
    report.append("1. **Re-engage VIPs** → recover 20-30% of lost revenue from high-risk customers.\n")
    report.append("2. **Loyalty program pilot** → +5-10% repeat purchase rate within 6 months.\n")
    report.append("3. **Fix fulfillment delays** → reduce cancellations by 1-2%.\n")
    report.append("\n---\n*Local analysis based on available data.*")
    return "\n".join(report)

def generate_deep_insights_with_persona(kpis, filters, daily_revenue, monthly_revenue, top_cities,
                                         revenue_categories, repeat_customers, clv_data, rfm_segments,
                                         cohort_retention, anomalies, high_risk, extra_metrics,
                                         persona="balanced_analyst"):
    one_time = 0
    repeat_cust = 0
    one_time = repeat_customers.get('one-time', repeat_customers.get('one_time',
               repeat_customers.get('One-Time', repeat_customers.get('One_Time', 0))))
    repeat_cust = repeat_customers.get('repeat', repeat_customers.get('repeat_customer',
                                          repeat_customers.get('Repeat', 0)))
    if one_time == 0:
        for k, v in repeat_customers.items():
            k_lower = str(k).lower().replace(' ', '').replace('-', '').replace('_', '')
            if 'one' in k_lower and 'time' in k_lower:
                one_time = v
                break
    if repeat_cust == 0:
        for k, v in repeat_customers.items():
            if 'repeat' in str(k).lower():
                repeat_cust = v
                break
    total_cust = one_time + repeat_cust
    repeat_rate = (repeat_cust / total_cust * 100) if total_cust else 0

    status_summary = get_status_summary(extra_metrics.get('order_status'))

    daily_vals = []
    for d in daily_revenue[-5:]:
        val = d.get('total_amount') or d.get('revenue') or 0
        daily_vals.append(f"${val:,.0f}")
    daily_str = ", ".join(daily_vals) if daily_vals else "no data"

    monthly_str = ""
    for m in monthly_revenue[-6:]:
        month = m.get('year_month', 'unknown')
        rev = m.get('total_amount', 0)
        monthly_str += f"{month}: ${rev:,.0f}; "

    top_cities_str = ", ".join([f"{c.get('city', 'N/A')} (${c.get('total_revenue',0):,.0f})" for c in top_cities[:3]])
    categories_str = ", ".join([f"{c.get('category', 'N/A')} (${c.get('revenue',0):,.0f})" for c in revenue_categories[:3]])

    highest_clv_list = clv_data.get('highest', [])
    avg_top_clv = sum(c.get('total_net_amount', c.get('total_revenue', 0)) for c in highest_clv_list) / max(len(highest_clv_list), 1)
    rfm_sample = rfm_segments[:3] if rfm_segments else []
    rfm_str = ", ".join([str(s.get('segment', s.get('rfm_segment', 'unknown'))) for s in rfm_sample])
    anomaly_dates = [a.get('date', '')[:10] for a in anomalies[:3]]
    anomalies_str = f"{len(anomalies)} days, e.g. {', '.join(anomaly_dates)}" if anomalies else "none"
    high_risk_total = sum(c.get('monetary', 0) for c in high_risk[:5])
    high_risk_str = f"{len(high_risk)} customers, total at-risk ${high_risk_total:,.0f}" if high_risk else "none"
    cohort_str = ""
    for c in cohort_retention[:3]:
        cohort_str += f"{c.get('cohort_month', '')} month {c.get('month_number',0)}: {c.get('retention_rate',0)*100:.1f}%; "

    churn_rate_val = extra_metrics.get('churn_rate')
    top_payment = extra_metrics.get('top_payment_method', 'N/A')

    def safe_float(val, default=0.0):
        try:
            return float(val)
        except (TypeError, ValueError):
            return default
    def safe_int(val, default=0):
        try:
            return int(val)
        except (TypeError, ValueError):
            return default
    total_revenue = safe_float(kpis.get('total_revenue', 0))
    total_orders = safe_int(kpis.get('total_orders', 0))
    total_customers = safe_int(kpis.get('total_customers', 0))
    aov = safe_float(kpis.get('avg_order_value', 0))

    context = f"""
KPIs: Revenue ${total_revenue:,.0f}, Orders {total_orders:,}, Customers {total_customers:,}, AOV ${aov:,.0f}
Filters: Date {filters.get('dateRange',{}).get('min','any')} -> {filters.get('dateRange',{}).get('max','any')}, City {filters.get('selectedCity','any')}, Category {filters.get('selectedCategory','any')}
Daily Revenue (last 5 days): {daily_str}
Monthly Revenue (last 6 months): {monthly_str}
Top Cities: {top_cities_str}
Top Categories: {categories_str}
Repeat Rate: {repeat_rate:.1f}%
Avg CLV Top 5: ${avg_top_clv:,.0f}
RFM Segments: {rfm_str}
Cohort Retention (sample): {cohort_str}
Revenue Anomalies: {anomalies_str}
High Risk VIPs: {high_risk_str}
Order Status Distribution: {status_summary}
Top Payment Method: {top_payment}
Churn Rate: {churn_rate_val if churn_rate_val is not None else 'N/A'}%
"""
    base_prompt = PERSONA_TEMPLATES.get(persona, PERSONA_TEMPLATES["balanced_analyst"])
    full_prompt = f"""{base_prompt}

--- DATA ---
{context}
"""
    insights = call_ai_provider_with_timeout(full_prompt, timeout=30)
    if insights:
        required = ["Executive Summary", "Key Metrics", "Deep Dive", "Root Causes", "Actionable Recommendations", "Expected Business Impact"]
        if not any(sec in insights for sec in required):
            insights += "\n\n---\n*Note: Some sections may be abbreviated due to token limits.*"
        return insights + "\n\n---\n*Powered by AI*"
    else:
        return generate_local_deep_insights_fallback(
            kpis, filters, daily_revenue, monthly_revenue, top_cities,
            revenue_categories, repeat_customers, clv_data, rfm_segments,
            cohort_retention, anomalies, high_risk, extra_metrics
        )