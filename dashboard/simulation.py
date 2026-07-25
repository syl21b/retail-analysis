import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LinearRegression
import database   # <-- import the module, not the variable
import logging

logger = logging.getLogger(__name__)

SIMULATION_COEFFS = {
    "repeat_rate": 1.2,
    "aov": 1.0,
    "churn_rate": 0.8,
    "fulfillment_days": 0.5,
    "last_trained": None
}

def compute_monthly_metrics():
    query = """
    WITH monthly_orders AS (
        SELECT 
            EXTRACT(YEAR FROM order_date) AS year,
            EXTRACT(MONTH FROM order_date) AS month,
            customer_id,
            order_id,
            net_amount
        FROM public.fact_orders
        WHERE order_date IS NOT NULL
    ),
    customer_monthly AS (
        SELECT 
            year, month,
            customer_id,
            COUNT(DISTINCT order_id) AS order_count,
            SUM(net_amount) AS customer_revenue
        FROM monthly_orders
        GROUP BY year, month, customer_id
    ),
    monthly_agg AS (
        SELECT 
            year, month,
            COUNT(DISTINCT customer_id) AS total_customers,
            COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_id END) AS repeat_customers,
            SUM(customer_revenue) AS total_revenue,
            COUNT(*) AS total_orders
        FROM customer_monthly
        GROUP BY year, month
    )
    SELECT 
        TO_CHAR(TO_DATE(year || '-' || month || '-01', 'YYYY-MM-DD'), 'YYYY-MM') AS year_month,
        total_revenue,
        (repeat_customers::float / NULLIF(total_customers, 0)) * 100 AS repeat_rate,
        (total_revenue / NULLIF(total_orders, 0)) AS aov
    FROM monthly_agg
    ORDER BY year, month;
    """
    try:
        rows = database.db.execute_query(query)   # <-- use database.db
        if not rows:
            raise Exception("No monthly data found")
        df = pd.DataFrame(rows)
        df['churn_rate'] = np.maximum(0, 100 - df['repeat_rate'] * 1.5)
        return df
    except Exception as e:
        logger.error(f"Failed to compute monthly metrics: {e}")
        return pd.DataFrame()

def train_simulation_model():
    df = compute_monthly_metrics()
    if df.empty or len(df) < 3:
        logger.warning("Not enough monthly data to train simulation model. Using default coefficients.")
        return
    df = df.sort_values('year_month')
    df['revenue_pct'] = df['total_revenue'].pct_change() * 100
    df['repeat_rate_pct'] = df['repeat_rate'].pct_change() * 100
    df['aov_pct'] = df['aov'].pct_change() * 100
    df['churn_rate_pct'] = df['churn_rate'].pct_change() * 100
    numeric_cols = ['revenue_pct', 'repeat_rate_pct', 'aov_pct', 'churn_rate_pct']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df_clean = df.replace([np.inf, -np.inf], np.nan).dropna(subset=numeric_cols)
    if len(df_clean) < 2:
        logger.warning("Not enough clean monthly data points for regression. Using default coefficients.")
        return
    X_repeat = df_clean['repeat_rate_pct'].values.reshape(-1, 1).astype(float)
    y_revenue = df_clean['revenue_pct'].values.astype(float)
    if len(X_repeat) >= 2:
        model = LinearRegression()
        model.fit(X_repeat, y_revenue)
        SIMULATION_COEFFS["repeat_rate"] = float(model.coef_[0])
        logger.info(f"Trained repeat_rate coefficient: {SIMULATION_COEFFS['repeat_rate']:.4f}")
    X_aov = df_clean['aov_pct'].values.reshape(-1, 1).astype(float)
    if len(X_aov) >= 2:
        model = LinearRegression()
        model.fit(X_aov, y_revenue)
        SIMULATION_COEFFS["aov"] = float(model.coef_[0])
        logger.info(f"Trained aov coefficient: {SIMULATION_COEFFS['aov']:.4f}")
    X_churn = df_clean['churn_rate_pct'].values.reshape(-1, 1).astype(float)
    if len(X_churn) >= 2:
        model = LinearRegression()
        model.fit(X_churn, y_revenue)
        SIMULATION_COEFFS["churn_rate"] = -float(model.coef_[0])
        logger.info(f"Trained churn_rate coefficient: {SIMULATION_COEFFS['churn_rate']:.4f}")
    SIMULATION_COEFFS["last_trained"] = datetime.now().isoformat()