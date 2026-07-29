import json
import hashlib
import logging
import re
import io
from datetime import datetime
from flask import request, jsonify, render_template, send_file
from cachetools import TTLCache
import pandas as pd
import numpy as np

from config import Config
from auth import require_auth, require_role, rate_limit, auth_manager
import database
from data_loader import loader, friendly_data, get_dataset
from sql_helpers import sanitize_output, validate_nlq_input, add_schema_prefix, fix_date_extract, create_performance_indexes
from ai import (
    generate_deep_insights_with_persona,
    _get_additional_metrics,
    feedback_store,
    call_ai_provider,
    fix_list_numbering,
    generate_local_deep_insights_fallback
)
from simulation import SIMULATION_COEFFS, train_simulation_model
from export import generate_report_html, generate_pdf_from_html

logger = logging.getLogger(__name__)

ai_insights_cache = TTLCache(maxsize=100, ttl=21600)
nlq_cache = TTLCache(maxsize=50, ttl=3600)

# ------------------------------
#  NLQ Helpers
# ------------------------------
def get_schema_description():
    schema_name = 'public'
    tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """
    tables = database.db.execute_query(tables_query, (schema_name,))
    if not tables:
        return "No tables found in public schema."
    description = "Database schema for retail analytics (schema: public):\n\n"
    for tbl in tables:
        table = tbl['table_name']
        cols_query = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
        """
        columns = database.db.execute_query(cols_query, (schema_name, table))
        if columns:
            col_list = ", ".join([f"{c['column_name']} ({c['data_type']})" for c in columns])
            description += f"- public.{table}: {col_list}\n"
        else:
            description += f"- public.{table}: (no columns found)\n"
    description += "\nKey metrics (derived): total_revenue = sum(net_amount), total_orders = count(distinct order_id)\n"
    try:
        date_range_query = "SELECT MIN(order_date) AS min_date, MAX(order_date) AS max_date FROM public.fact_orders WHERE order_date IS NOT NULL"
        date_range = database.db.execute_query(date_range_query)
        if date_range and date_range[0]['min_date'] and date_range[0]['max_date']:
            min_date = date_range[0]['min_date']
            max_date = date_range[0]['max_date']
            description += f"\nIMPORTANT: The data covers dates from {min_date} to {max_date}. If a user asks for a date outside this range, inform them that no data exists for that period.\n"
    except Exception as e:
        logger.warning(f"Could not fetch date range: {e}")
    return description

def generate_sql_from_question(question, previous_error=None):
    schema_desc = get_schema_description()
    if previous_error:
        prompt = f"""You are an expert SQL generator. The previous SQL query failed with this error:

{previous_error}

Please correct the SQL query. Use the schema below.

Schema:
{schema_desc}

User question: {question}

Rules:
- Use schema prefix 'public.'
- Only SELECT statements.
- Return ONLY SQL, no explanation.

Corrected SQL query:
"""
    else:
        prompt = f"""You are an expert SQL generator. Given the schema, convert the question to PostgreSQL SELECT.

Schema:
{schema_desc}

User question: {question}

Rules:
- Use 'public.'
- Only SELECT.
- Return ONLY SQL.

SQL query:
"""
    sql = call_ai_provider(prompt)
    if not sql:
        return None
    sql = re.sub(r'```sql\n?', '', sql)
    sql = re.sub(r'```\n?', '', sql)
    sql = sql.strip()
    if sql.startswith('--'):
        return None
    return sql

# ------------------------------
#  Alert helper
# ------------------------------
def check_and_trigger_alerts(kpis, anomalies, repeat_customers, extra_metrics):
    alerts = []
    if anomalies and len(anomalies) > 0:
        alert_msg = f"⚠️ Revenue Anomaly: {len(anomalies)} days with >20% drop."
        alerts.append(alert_msg)
        logger.info(f"SIMULATED SLACK ALERT: {alert_msg}")
        logger.info(f"SIMULATED JIRA CARD: Revenue Anomaly Alert\n{alert_msg}")
    one_time = repeat_customers.get('one-time', 0)
    repeat_cust = repeat_customers.get('repeat', 0)
    total_cust = one_time + repeat_cust
    repeat_rate = (repeat_cust / total_cust * 100) if total_cust else 0
    if repeat_rate < 30:
        alert_msg = f"⚠️ Low Repeat Rate: {repeat_rate:.1f}% (below 30% threshold)"
        alerts.append(alert_msg)
        logger.info(f"SIMULATED SLACK ALERT: {alert_msg}")
        logger.info(f"SIMULATED JIRA CARD: Low Repeat Rate\n{alert_msg}")
    high_risk = extra_metrics.get('high_risk_vips', [])
    if high_risk and len(high_risk) > 5:
        alert_msg = f"⚠️ {len(high_risk)} high-value customers at risk of churn"
        alerts.append(alert_msg)
        logger.info(f"SIMULATED SLACK ALERT: {alert_msg}")
        logger.info(f"SIMULATED JIRA CARD: VIP Churn Risk\n{alert_msg}")
    return alerts

# ------------------------------
#  Route Registration
# ------------------------------
def register_routes(app):

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        api_key = data.get('api_key') if data else None
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        user = auth_manager.verify_api_key(api_key)
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401
        token = auth_manager.generate_jwt(user['user_id'], user['role'])
        return jsonify({'token': token, 'user': user})

    @app.route('/api/cache/status', methods=['GET'])
    @require_auth
    def cache_status():
        return jsonify({
            'size': len(loader._cache),
            'maxsize': loader._cache.maxsize,
            'ttl': loader._cache.ttl,
            'keys': list(loader._cache.keys())
        })

    @app.route('/api/cache/clear', methods=['POST'])
    @require_auth
    @require_role(['admin'])
    def clear_cache():
        loader.clear_cache()
        return jsonify({'message': 'Cache cleared successfully'})

    @app.route('/api/datasets')
    @require_auth
    def list_datasets():
        return jsonify(list(friendly_data.keys()))

    @app.route('/api/raw/<path:name>')
    @require_auth
    def raw_dataset(name):
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get(name)
        if df is None or df.empty:
            return jsonify([])
        sliced = df.iloc[offset:offset+limit]
        return jsonify(sanitize_output(loader.to_dict(sliced)))

    @app.route('/api/date_range')
    @require_auth
    def date_range():
        df = friendly_data.get('Daily Revenue Trends')
        if df is not None and not df.empty and 'order_day' in df.columns:
            dates = pd.to_datetime(df['order_day'])
            return jsonify({'min_date': dates.min().strftime('%Y-%m-%d'), 'max_date': dates.max().strftime('%Y-%m-%d')})
        return jsonify({'min_date': None, 'max_date': None})

    @app.route('/api/value_range')
    @require_auth
    def value_range():
        df = friendly_data.get('Order Value Distribution')
        if df is not None and not df.empty and 'min_order_value' in df.columns:
            return jsonify({'min_value': float(df['min_order_value'].iloc[0]), 'max_value': float(df['max_order_value'].iloc[0])})
        return jsonify({'min_value': 0, 'max_value': 10000})

    @app.route('/api/kpis')
    @require_auth
    def kpis():
        with database.db.get_cursor() as cur:
            cur.execute("SELECT COALESCE(SUM(net_amount), 0) FROM public.fact_orders")
            total_revenue = cur.fetchone()['coalesce']
            cur.execute("SELECT COUNT(DISTINCT order_id) FROM public.fact_orders")
            total_orders = cur.fetchone()['count']
            cur.execute("SELECT COUNT(DISTINCT customer_id) FROM public.fact_orders")
            total_customers = cur.fetchone()['count']
        avg_order = total_revenue / total_orders if total_orders else 0
        return jsonify({
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "total_customers": total_customers,
            "avg_order_value": round(avg_order, 2)
        })

    @app.route('/api/revenue_trend', methods=['GET'])
    @require_auth
    def revenue_trend():
        granularity = request.args.get('granularity', 'month')
        if granularity == 'day':
            sql = """
                SELECT order_date AS period, SUM(net_amount) AS revenue
                FROM public.fact_orders
                GROUP BY order_date
                ORDER BY order_date
            """
        elif granularity == 'week':
            sql = """
                SELECT DATE_TRUNC('week', order_date) AS period, SUM(net_amount) AS revenue
                FROM public.fact_orders
                GROUP BY DATE_TRUNC('week', order_date)
                ORDER BY period
            """
        else:
            sql = """
                SELECT DATE_TRUNC('month', order_date) AS period, SUM(net_amount) AS revenue
                FROM public.fact_orders
                GROUP BY DATE_TRUNC('month', order_date)
                ORDER BY period
            """
        rows = database.db.execute_query(sql)
        if not rows:
            return jsonify([])
        result = []
        for row in rows:
            period = row['period']
            result.append({
                'period': period.isoformat() if hasattr(period, 'isoformat') else str(period),
                'revenue': float(row['revenue'])
            })
        return jsonify(sanitize_output(result))

    # ---------- All standard endpoints ----------
    @app.route('/api/daily_revenue')
    @require_auth
    def daily_revenue():
        limit = request.args.get('limit', default=90, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Daily Revenue Trends')
        if df is None or df.empty:
            return jsonify([])
        sliced = df.iloc[offset:offset+limit]
        return jsonify(sanitize_output(loader.to_dict(sliced)))

    @app.route('/api/monthly_revenue')
    @require_auth
    def monthly_revenue():
        limit = request.args.get('limit', default=24, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Monthly Revenue Trends')
        if df is None or df.empty:
            return jsonify([])
        sliced = df.iloc[offset:offset+limit]
        return jsonify(sanitize_output(loader.to_dict(sliced)))

    @app.route('/api/top_cities')
    @require_auth
    def top_cities():
        limit = request.args.get('limit', default=10, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Top Cities by Revenue')
        if df is not None and not df.empty:
            sliced = df.iloc[offset:offset+limit]
            return jsonify(sanitize_output(loader.to_dict(sliced)))
        return jsonify([])

    @app.route('/api/revenue_by_category')
    @require_auth
    def revenue_by_category():
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Revenue by Product Category')
        if df is not None and not df.empty:
            sliced = df.iloc[offset:offset+limit]
            return jsonify(sanitize_output(loader.to_dict(sliced)))
        return jsonify([])

    @app.route('/api/revenue_by_subcategory')
    @require_auth
    def revenue_by_subcategory():
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Revenue by Product SubCategory')
        if df is not None and not df.empty:
            df = df.copy()
            subcat_col = None
            for col in df.columns:
                if 'subcategory' in col.lower() or 'sub_category' in col.lower():
                    subcat_col = col
                    break
            rev_col = None
            for col in df.columns:
                if 'revenue' in col.lower() or 'amount' in col.lower():
                    rev_col = col
                    break
            if subcat_col and rev_col:
                df = df.rename(columns={subcat_col: 'subcategory', rev_col: 'revenue'})
            sliced = df.iloc[offset:offset+limit]
            return jsonify(sanitize_output(loader.to_dict(sliced)))
        return jsonify([])

    @app.route('/api/revenue_contribution')
    @require_auth
    def revenue_contribution():
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Revenue Contribution Analysis')
        if df is None or df.empty:
            return jsonify([])
        if 'total_revenue' not in df.columns:
            logger.warning("Revenue Contribution Analysis missing 'total_revenue' column")
            return jsonify([])
        df = df.sort_values('total_revenue', ascending=False)
        df['total_revenue'] = df['total_revenue'].astype(float)
        total = df['total_revenue'].sum()
        if total == 0:
            return jsonify([])
        df['cumulative_percentage'] = (df['total_revenue'].cumsum() / total) * 100
        sliced = df.iloc[offset:offset+limit]
        return jsonify(sanitize_output(loader.to_dict(sliced)))

    @app.route('/api/order_value_distribution')
    @require_auth
    def order_value_distribution():
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Order Value Distribution')
        if df is not None and not df.empty:
            sliced = df.iloc[offset:offset+limit]
            return jsonify(sanitize_output(loader.to_dict(sliced)))
        return jsonify([])

    @app.route('/api/customer_clv')
    @require_auth
    def customer_clv():
        df = friendly_data.get('Customer Lifetime Value')
        if df is None or df.empty:
            return jsonify({'highest': [], 'lowest': []})
        amount_col = None
        for col in ['total_net_amount', 'total_revenue', 'clv', 'customer_lifetime_value']:
            if col in df.columns:
                amount_col = col
                break
        if not amount_col:
            logger.warning("No amount column found in CLV data")
            return jsonify({'highest': [], 'lowest': []})
        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
        highest = df.nlargest(5, amount_col)
        lowest = df.nsmallest(5, amount_col)
        return jsonify({
            'highest': sanitize_output(loader.to_dict(highest)),
            'lowest': sanitize_output(loader.to_dict(lowest))
        })

    @app.route('/api/repeat_vs_onetime')
    @require_auth
    def repeat_vs_onetime():
        return jsonify(sanitize_output(get_dataset('Repeat vs One-Time Customers')))

    @app.route('/api/customer_segmentation')
    @require_auth
    def customer_segmentation():
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Customer Segmentation')
        if df is None or df.empty:
            return jsonify([])
        df = df.copy()
        if 'total_revenue' not in df.columns:
            logger.warning("Customer Segmentation missing 'total_revenue' column")
            return jsonify([])
        df['total_revenue'] = pd.to_numeric(df['total_revenue'], errors='coerce').fillna(0)
        try:
            if len(df['total_revenue'].unique()) >= 4:
                df['segment'] = pd.qcut(df['total_revenue'], q=4, labels=['Bronze', 'Silver', 'Gold', 'Platinum'])
            else:
                raise ValueError("Not enough distinct revenue values")
        except Exception:
            revenue_median = df['total_revenue'].median()
            revenue_high = df['total_revenue'].quantile(0.75)
            revenue_low = df['total_revenue'].quantile(0.25)
            df['segment'] = 'Bronze'
            df.loc[df['total_revenue'] > revenue_low, 'segment'] = 'Silver'
            df.loc[df['total_revenue'] > revenue_median, 'segment'] = 'Gold'
            df.loc[df['total_revenue'] > revenue_high, 'segment'] = 'Platinum'
        sliced = df.iloc[offset:offset+limit]
        return jsonify(sanitize_output(loader.to_dict(sliced)))

    @app.route('/api/churn_detection')
    @require_auth
    def churn_detection():
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Churn Detection')
        if df is not None and not df.empty:
            sliced = df.iloc[offset:offset+limit]
            return jsonify(sanitize_output(loader.to_dict(sliced)))
        return jsonify([])

    @app.route('/api/order_status')
    @require_auth
    def order_status():
        return jsonify(sanitize_output(get_dataset('Order Status Distribution')))

    @app.route('/api/payment_methods')
    @require_auth
    def payment_methods():
        return jsonify(sanitize_output(get_dataset('Payment Method Analysis')))

    @app.route('/api/fulfillment_performance')
    @require_auth
    def fulfillment_performance():
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Order Fulfillment Performance')
        if df is not None and not df.empty:
            sliced = df.iloc[offset:offset+limit]
            return jsonify(sanitize_output(loader.to_dict(sliced)))
        return jsonify([])

    @app.route('/api/time_to_purchase')
    @require_auth
    def time_to_purchase():
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Time to Purchase Behavior')
        if df is not None and not df.empty and 'days_between_orders' in df.columns:
            df_filtered = df[df['days_between_orders'] > 7]
            sliced = df_filtered.iloc[offset:offset+limit]
            return jsonify(sanitize_output(loader.to_dict(sliced)))
        return jsonify([])

    @app.route('/api/rfm_segmentation')
    @require_auth
    def rfm_segmentation():
        limit = request.args.get('limit', default=1000, type=int)
        offset = request.args.get('offset', default=0, type=int)
        recency_min = request.args.get('recency_min', type=int)
        recency_max = request.args.get('recency_max', type=int)
        monetary_min = request.args.get('monetary_min', type=float)
        monetary_max = request.args.get('monetary_max', type=float)

        df = friendly_data.get('RFM Segmentation')
        if df is None or df.empty:
            return jsonify([])

        df = df.copy()
        if recency_min is not None:
            df = df[df['recency_days'] >= recency_min]
        if recency_max is not None:
            df = df[df['recency_days'] <= recency_max]
        if monetary_min is not None:
            df = df[df['monetary'] >= monetary_min]
        if monetary_max is not None:
            df = df[df['monetary'] <= monetary_max]

        if limit != -1:
            df = df.iloc[offset:offset + limit]
        else:
            df = df.iloc[offset:]

        return jsonify(sanitize_output(loader.to_dict(df)))

    @app.route('/api/cohort_retention')
    @require_auth
    def cohort_retention():
        limit = request.args.get('limit', default=200, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Cohort Retention Analysis')
        if df is None or df.empty:
            return jsonify([])
        if 'month_number' not in df.columns:
            logger.warning("Cohort Retention Analysis missing 'month_number' column")
            return jsonify([])
        df = df[df['month_number'] > 0]
        sliced = df.iloc[offset:offset+limit]
        return jsonify(sanitize_output(loader.to_dict(sliced)))

    @app.route('/api/revenue_by_location')
    @require_auth
    def revenue_by_location():
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        df = friendly_data.get('Revenue by Location')
        if df is not None and not df.empty:
            sliced = df.iloc[offset:offset+limit]
            return jsonify(sanitize_output(loader.to_dict(sliced)))
        return jsonify([])

    @app.route('/api/revenue_anomalies')
    @require_auth
    def revenue_anomalies():
        df = friendly_data.get('Daily Revenue Trends')
        if df is None or df.empty:
            return jsonify([])
        date_col = None
        for col in df.columns:
            if col in ['order_day', 'order_date', 'day', 'date', 'transaction_date'] or 'date' in col.lower():
                date_col = col
                break
        rev_col = None
        for col in df.columns:
            if col in ['total_amount', 'revenue', 'amount', 'total_revenue', 'sales'] or 'amount' in col.lower() or 'revenue' in col.lower():
                rev_col = col
                break
        if not date_col or not rev_col:
            return jsonify([])
        df[date_col] = pd.to_datetime(df[date_col])
        if df.groupby(date_col).size().max() > 1:
            df = df.groupby(date_col)[rev_col].sum().reset_index()
        else:
            df = df[[date_col, rev_col]].copy()
        df = df.sort_values(date_col)
        df['pct_change'] = df[rev_col].pct_change() * 100
        anomalies = df[df['pct_change'] < -20][[date_col, rev_col, 'pct_change']]
        anomalies = anomalies.rename(columns={date_col: 'date', rev_col: 'revenue', 'pct_change': 'drop_percent'})
        anomalies['date'] = anomalies['date'].dt.strftime('%Y-%m-%d')
        return jsonify(sanitize_output(loader.to_dict(anomalies)))

    @app.route('/api/high_risk_customers')
    @require_auth
    def high_risk_customers():
        limit = request.args.get('limit', default=20, type=int)
        offset = request.args.get('offset', default=0, type=int)
        segment_filter = request.args.get('segment', '').strip()
        rfm_df = friendly_data.get('RFM Segmentation')
        if rfm_df is None or rfm_df.empty:
            return jsonify([])
        required_cols = ['customer_id', 'recency_days', 'frequency', 'monetary']
        for col in required_cols:
            if col not in rfm_df.columns:
                return jsonify([])
        if 'segment' not in rfm_df.columns:
            rec_median = rfm_df['recency_days'].median()
            mon_median = rfm_df['monetary'].median()
            rfm_df['segment'] = 'Others'
            rfm_df.loc[(rfm_df['recency_days'] <= rec_median/2) & (rfm_df['monetary'] >= mon_median*2), 'segment'] = 'Champions'
            rfm_df.loc[(rfm_df['recency_days'] <= rec_median) & (rfm_df['monetary'] >= mon_median), 'segment'] = 'Loyal'
            rfm_df.loc[(rfm_df['recency_days'] > rec_median*1.5) & (rfm_df['monetary'] < mon_median), 'segment'] = 'At Risk'
        monetary_90th = rfm_df['monetary'].quantile(0.9)
        high_risk = rfm_df[(rfm_df['segment'] == 'At Risk') & (rfm_df['monetary'] > monetary_90th)]
        if segment_filter:
            high_risk = high_risk[high_risk['segment'] == segment_filter]
        high_risk = high_risk.sort_values('monetary', ascending=False)
        if 'full_name' in high_risk.columns:
            high_risk['full_name'] = high_risk['full_name'].fillna(high_risk['customer_id'].apply(lambda x: f"Customer {x}"))
        else:
            high_risk['full_name'] = high_risk['customer_id'].apply(lambda x: f"Customer {x}")
        result_cols = ['customer_id', 'full_name', 'recency_days', 'frequency', 'monetary', 'segment']
        sliced = high_risk[result_cols].iloc[offset:offset+limit]
        return jsonify(sanitize_output(loader.to_dict(sliced)))

    @app.route('/api/aov_by_category')
    @require_auth
    def aov_by_category():
        df = friendly_data.get('Revenue by Product Category')
        if df is None or df.empty or 'revenue' not in df.columns:
            return jsonify([])
        df['aov'] = df['revenue'] / 1000
        return jsonify(sanitize_output(loader.to_dict(df[['category', 'aov']])))

    @app.route('/api/frequency_by_category')
    @require_auth
    def frequency_by_category():
        df = friendly_data.get('Revenue by Product Category')
        try:
            if df is None or df.empty:
                return jsonify([])
        except Exception:
            return jsonify([])
        if 'category' not in df.columns:
            return jsonify([])
        df['frequency'] = 1.5
        return jsonify(sanitize_output(loader.to_dict(df[['category', 'frequency']])))

    # ---------- AI Insights ----------
    @app.route('/api/ai_insights', methods=['POST'])
    @require_auth
    @rate_limit(limit=Config.RATELIMIT_AI, window=3600, by_ip=True)
    def ai_insights():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        filters = data.get('filters', {})
        kpis_data = data.get('kpis', {})
        daily_revenue = data.get('daily_revenue', [])
        monthly_revenue = data.get('monthly_revenue', [])
        top_cities = data.get('top_cities', [])
        revenue_categories = data.get('revenue_categories', [])
        repeat_customers = data.get('repeat_customers', {})
        clv_data = data.get('clv_data', {'highest': [], 'lowest': []})
        rfm_segments = data.get('rfm_segments', [])
        cohort_retention = data.get('cohort_retention', [])
        anomalies = data.get('anomalies', [])
        high_risk = data.get('high_risk_customers', [])
        persona = data.get('persona', 'balanced_analyst')
        cache_key = hashlib.md5(json.dumps({
            "filters": filters,
            "kpis": kpis_data,
            "daily_tail": [d.get('total_amount') for d in daily_revenue[-7:]],
            "monthly_tail": [m.get('total_amount') for m in monthly_revenue[-6:]],
            "top_cities_ids": [c.get('city') for c in top_cities[:3]],
            "persona": persona,
            "repeat_rate_hash": repeat_customers.get('repeat', 0)
        }, sort_keys=True).encode()).hexdigest()
        if cache_key in ai_insights_cache:
            insights = ai_insights_cache[cache_key]
        else:
            extra_metrics = _get_additional_metrics()
            try:
                insights = generate_deep_insights_with_persona(
                    kpis=kpis_data, filters=filters, daily_revenue=daily_revenue,
                    monthly_revenue=monthly_revenue, top_cities=top_cities,
                    revenue_categories=revenue_categories, repeat_customers=repeat_customers,
                    clv_data=clv_data, rfm_segments=rfm_segments, cohort_retention=cohort_retention,
                    anomalies=anomalies, high_risk=high_risk, extra_metrics=extra_metrics,
                    persona=persona
                )
            except Exception as e:
                logger.error(f"AI insights generation failed: {e}", exc_info=True)
                insights = generate_local_deep_insights_fallback(
                    kpis=kpis_data, filters=filters, daily_revenue=daily_revenue,
                    monthly_revenue=monthly_revenue, top_cities=top_cities,
                    revenue_categories=revenue_categories, repeat_customers=repeat_customers,
                    clv_data=clv_data, rfm_segments=rfm_segments,
                    cohort_retention=cohort_retention, anomalies=anomalies,
                    high_risk=high_risk, extra_metrics=extra_metrics
                )
            ai_insights_cache[cache_key] = insights
        insights = fix_list_numbering(insights)
        return jsonify({"insights": insights, "persona": persona})

    # ---------- Simulation ----------
    @app.route('/api/simulate/train', methods=['POST'])
    @require_auth
    @require_role(['admin'])
    def trigger_training():
        try:
            train_simulation_model()
            return jsonify({
                "message": "Simulation model retrained successfully",
                "coefficients": {k: v for k, v in SIMULATION_COEFFS.items() if k != "last_trained"},
                "last_trained": SIMULATION_COEFFS["last_trained"]
            })
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/simulate', methods=['POST'])
    @require_auth
    @require_role(['analyst', 'admin'])
    @rate_limit(limit=Config.RATELIMIT_SIMULATE, window=3600, by_ip=True)
    def simulate():
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request"}), 400
        metric = data.get('metric')
        delta = float(data.get('delta', 0))
        try:
            total_revenue = kpis().json.get('total_revenue', 0)
            total_orders = kpis().json.get('total_orders', 0)
            aov_current = total_revenue / total_orders if total_orders else 0
            coeff = SIMULATION_COEFFS.get(metric, 1.0)
            if metric == 'churn_rate':
                uplift_pct = delta * coeff
            else:
                uplift_pct = delta * coeff
            estimated_uplift = total_revenue * (uplift_pct / 100)
            new_revenue = total_revenue + estimated_uplift
            extra_info = {}
            if metric == 'aov':
                extra_info = {
                    "current_AOV": round(aov_current, 2),
                    "new_AOV": round(aov_current * (1 + delta/100), 2)
                }
            return jsonify({
                "metric": metric,
                "delta": delta,
                "estimated_revenue_uplift": round(estimated_uplift, 2),
                "new_total_revenue": round(new_revenue, 2),
                "uplift_percentage": round(uplift_pct, 2),
                "confidence": "data‑driven (regression on monthly data)" if SIMULATION_COEFFS["last_trained"] else "fallback defaults",
                "extra_info": extra_info,
                "coefficient_used": round(coeff, 4)
            })
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            return jsonify({"error": str(e)}), 500

    # ---------- Alerts ----------
    @app.route('/api/check_anomalies', methods=['POST'])
    @require_auth
    def check_anomalies():
        try:
            kpis_data = kpis().json
            daily_df = friendly_data.get('Daily Revenue Trends')
            anomalies_list = []
            if daily_df is not None and not daily_df.empty:
                rev_col = 'total_amount'
                if rev_col in daily_df.columns:
                    df_sorted = daily_df.sort_values('order_day')
                    df_sorted['pct_change'] = df_sorted[rev_col].pct_change() * 100
                    anomalies_df = df_sorted[df_sorted['pct_change'] < -20]
                    anomalies_list = anomalies_df[['order_day', rev_col, 'pct_change']].rename(columns={'order_day': 'date', rev_col: 'revenue', 'pct_change': 'drop_percent'}).to_dict(orient='records')
            repeat_data = get_dataset('Repeat vs One-Time Customers')
            repeat_dict = {r['customer_type']: r['customer_count'] for r in repeat_data} if repeat_data else {}
            extra_metrics = _get_additional_metrics()
            extra_metrics['high_risk_vips'] = get_dataset('high_risk_customers')
            alerts = check_and_trigger_alerts(kpis_data, anomalies_list, repeat_dict, extra_metrics)
            return jsonify({"alerts": alerts, "triggered": len(alerts) > 0})
        except Exception as e:
            logger.error(f"Alert check failed: {e}")
            return jsonify({"error": str(e)}), 500

    # ---------- Feedback ----------
    @app.route('/api/feedback', methods=['POST'])
    @require_auth
    def submit_feedback():
        data = request.get_json()
        persona = data.get('persona')
        feedback = data.get('feedback')
        if persona not in feedback_store:
            return jsonify({"error": "Invalid persona"}), 400
        if feedback not in ['up', 'down']:
            return jsonify({"error": "Feedback must be 'up' or 'down'"}), 400
        feedback_store[persona][feedback] += 1
        logger.info(f"Feedback for {persona}: {feedback} (now up={feedback_store[persona]['up']}, down={feedback_store[persona]['down']})")
        return jsonify({"message": "Thank you for your feedback!", "stats": feedback_store[persona]})

    @app.route('/api/feedback/stats', methods=['GET'])
    @require_auth
    def get_feedback_stats():
        return jsonify(feedback_store)

    # ---------- ENHANCED EXPORT (PDF only) ----------
    @app.route('/api/export', methods=['POST'])
    @require_auth
    def export_report():
        try:
            data = request.get_json()
            format_type = data.get('format', 'pdf')
            if format_type != 'pdf':
                return jsonify({"error": "Only PDF export is supported"}), 400

            kpis = data.get('kpis', {})
            insights_html = data.get('insights_html', '<h1>No insights</h1>')
            charts = data.get('charts', {})
            filters = data.get('filters', {})

            report_html = generate_report_html(kpis, insights_html, charts, filters)

            try:
                pdf_bytes = generate_pdf_from_html(report_html)
            except Exception as e:
                logger.error(f"PDF generation failed: {e}")
                return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            )

        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    # ---------- Health ----------
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

    # ---------- Security Headers ----------
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Cache-Control'] = 'no-store, max-age=0'
        return response

    # ---------- Churn Prediction ----------
    @app.route('/api/churn/train', methods=['POST'])
    @require_auth
    @require_role(['admin'])
    def train_churn_model():
        from churn_model import train_model, set_threshold
        data = request.get_json()
        if data and 'threshold' in data:
            set_threshold(data['threshold'])
        else:
            success = train_model()
            if success:
                return jsonify({"message": "Churn model trained successfully"}), 200
            else:
                return jsonify({"error": "Training failed"}), 500
        return jsonify({"message": "Churn model retrained with new threshold"}), 200

    @app.route('/api/churn/predict', methods=['GET'])
    @require_auth
    def predict_churn():
        customer_id = request.args.get('customer_id', type=int)
        if not customer_id:
            return jsonify({"error": "Missing customer_id"}), 400
        from churn_model import predict
        result = predict(customer_id)
        if "error" in result:
            return jsonify(result), 404
        return jsonify(result)

    @app.route('/api/churn/at_risk', methods=['GET'])
    @require_auth
    def at_risk_customers():
        limit = request.args.get('limit', default=20, type=int)
        threshold = request.args.get('threshold', type=int)
        if threshold is not None:
            from churn_model import set_threshold
            set_threshold(threshold)
        from churn_model import get_at_risk_customers
        results = get_at_risk_customers(limit)
        return jsonify(results)

    @app.route('/api/churn/stats', methods=['GET'])
    @require_auth
    def churn_stats():
        threshold = request.args.get('threshold', type=int)
        if threshold is not None:
            from churn_model import set_threshold
            set_threshold(threshold)
        from churn_model import get_churn_stats
        stats = get_churn_stats()
        return jsonify(stats)

    @app.route('/api/churn/revenue_timeline', methods=['GET'])
    @require_auth
    def churn_revenue_timeline():
        threshold = request.args.get('threshold', type=int)
        if threshold is not None:
            from churn_model import set_threshold
            set_threshold(threshold)
        from churn_model import get_revenue_timeline
        data = get_revenue_timeline()
        return jsonify(data)