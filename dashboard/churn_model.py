import logging
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib
import os

from .database import db

logger = logging.getLogger(__name__)

# Global model and scaler
_model = None
_scaler = None
_columns = None
_is_trained = False

# Mutable threshold
CHURN_THRESHOLD_DAYS = 180
MODEL_PATH = "churn_model.pkl"
SCALER_PATH = "scaler.pkl"

def set_threshold(days):
    """Update the churn threshold and retrain the model."""
    global CHURN_THRESHOLD_DAYS
    if days != CHURN_THRESHOLD_DAYS:
        CHURN_THRESHOLD_DAYS = days
        logger.info(f"Churn threshold changed to {days} days. Retraining model...")
        return train_model()
    return True

def _build_features():
    query = """
    WITH customer_orders AS (
        SELECT 
            customer_id,
            MIN(order_date) AS first_order,
            MAX(order_date) AS last_order,
            COUNT(DISTINCT order_id) AS frequency,
            SUM(net_amount) AS monetary
        FROM public.fact_orders
        GROUP BY customer_id
    ),
    order_dates AS (
        SELECT 
            customer_id,
            order_date,
            LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order_date
        FROM public.fact_orders
    ),
    gaps AS (
        SELECT 
            customer_id,
            AVG(order_date - prev_order_date) AS avg_days_between
        FROM order_dates
        WHERE prev_order_date IS NOT NULL
        GROUP BY customer_id
    )
    SELECT 
        co.customer_id,
        co.frequency,
        co.monetary,
        (NOW()::date - co.last_order) AS recency,
        (co.last_order - co.first_order) AS tenure,
        g.avg_days_between,
        co.monetary / NULLIF(co.frequency, 0) AS avg_order_value,
        CASE 
            WHEN (NOW()::date - co.last_order) > %s THEN 1 
            ELSE 0 
        END AS churn
    FROM customer_orders co
    LEFT JOIN gaps g ON co.customer_id = g.customer_id
    """
    try:
        rows = db.execute_query(query, (CHURN_THRESHOLD_DAYS,))
        df = pd.DataFrame(rows)
        df['avg_days_between'] = df['avg_days_between'].fillna(0)
        df['tenure'] = df['tenure'].fillna(0)
        for col in ['frequency', 'monetary', 'recency', 'tenure', 'avg_days_between', 'avg_order_value']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        logger.error(f"Failed to build features: {e}")
        return pd.DataFrame()

def train_model():
    global _model, _scaler, _columns, _is_trained
    df = _build_features()
    if df.empty:
        logger.warning("No data to train churn model.")
        return False

    X = df.drop(['customer_id', 'churn'], axis=1)
    y = df['churn']
    _columns = X.columns.tolist()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    report = classification_report(y_test, preds, output_dict=True)
    logger.info(f"Churn model training complete. Accuracy: {report['accuracy']:.3f}")
    if '1' in report:
        logger.info(f"Precision (churn): {report['1']['precision']:.3f}, Recall: {report['1']['recall']:.3f}")
    else:
        logger.info("No churned customers in test set – model may predict only one class.")

    _model = model
    _scaler = scaler
    _is_trained = True

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    logger.info(f"Model saved to {MODEL_PATH}")
    return True

def load_model():
    global _model, _scaler, _columns, _is_trained
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        try:
            _model = joblib.load(MODEL_PATH)
            _scaler = joblib.load(SCALER_PATH)
            _is_trained = True
            if hasattr(_scaler, 'feature_names_in_'):
                _columns = list(_scaler.feature_names_in_)
            else:
                _columns = None
                logger.warning("Columns not stored in scaler. Will retrain on next use.")
            logger.info("Churn model loaded from disk.")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
    return False

def _get_churn_probs(X_scaled):
    """Return churn probabilities regardless of number of classes."""
    probs = _model.predict_proba(X_scaled)
    if probs.shape[1] == 1:
        if _model.classes_[0] == 1:
            return probs[:, 0]
        else:
            return 1 - probs[:, 0]
    else:
        return probs[:, 1]

def predict(customer_id):
    if not _is_trained:
        if not load_model():
            train_model()
        if not _is_trained:
            return {"error": "Churn model not available"}

    df = _build_features()
    if df.empty:
        return {"error": "No data"}
    customer_row = df[df['customer_id'] == customer_id]
    if customer_row.empty:
        return {"error": f"Customer {customer_id} not found"}

    X = customer_row.drop(['customer_id', 'churn'], axis=1)
    if _columns is not None:
        X = X.reindex(columns=_columns, fill_value=0)
    X_scaled = _scaler.transform(X)

    churn_prob = _get_churn_probs(X_scaled)[0]
    risk = "High" if churn_prob > 0.7 else ("Medium" if churn_prob > 0.4 else "Low")

    return {
        "customer_id": customer_id,
        "churn_probability": round(churn_prob, 4),
        "churn_risk": risk,
        "features": customer_row.to_dict(orient='records')[0]
    }

def get_at_risk_customers(limit=20):
    if not _is_trained:
        if not load_model():
            train_model()
        if not _is_trained:
            return []

    df = _build_features()
    if df.empty:
        return []

    X = df.drop(['customer_id', 'churn'], axis=1)
    if _columns is not None:
        X = X.reindex(columns=_columns, fill_value=0)
    X_scaled = _scaler.transform(X)

    churn_probs = _get_churn_probs(X_scaled)

    df['churn_probability'] = churn_probs
    df['churn_risk'] = pd.cut(churn_probs, bins=[0, 0.4, 0.7, 1.0], labels=['Low', 'Medium', 'High'])
    top_risk = df.sort_values('churn_probability', ascending=False).head(limit)

    return top_risk[['customer_id', 'churn_probability', 'churn_risk', 'recency', 'frequency', 'monetary']].to_dict(orient='records')

def get_churn_stats():
    if not _is_trained:
        if not load_model():
            train_model()
        if not _is_trained:
            return {}

    df = _build_features()
    if df.empty:
        return {}

    X = df.drop(['customer_id', 'churn'], axis=1)
    if _columns is not None:
        X = X.reindex(columns=_columns, fill_value=0)
    X_scaled = _scaler.transform(X)

    churn_probs = _get_churn_probs(X_scaled)

    risk_categories = pd.cut(churn_probs, bins=[0, 0.4, 0.7, 1.0], labels=['Low', 'Medium', 'High'])
    risk_counts = risk_categories.value_counts().to_dict()

    actual_churn = df['churn'].sum()
    total_customers = len(df)

    return {
        "total_customers": total_customers,
        "actual_churned": int(actual_churn),
        "churn_rate": round(actual_churn / total_customers * 100, 2) if total_customers else 0,
        "risk_distribution": {k: int(v) for k, v in risk_counts.items()},
        "avg_probability": float(churn_probs.mean())
    }

def get_revenue_timeline():
    """
    Return monthly revenue and churn rate (actual churned % based on threshold).
    """
    query = """
    WITH monthly_data AS (
        SELECT 
            DATE_TRUNC('month', order_date) AS month,
            SUM(net_amount) AS revenue,
            COUNT(DISTINCT customer_id) AS active_customers
        FROM public.fact_orders
        GROUP BY month
    ),
    last_orders AS (
        SELECT 
            customer_id,
            MAX(order_date) AS last_order_date
        FROM public.fact_orders
        GROUP BY customer_id
    ),
    churned_customers AS (
        SELECT 
            DATE_TRUNC('month', last_order_date) AS month,
            COUNT(*) AS churned_count
        FROM last_orders
        WHERE (NOW()::date - last_order_date) > %s
        GROUP BY month
    )
    SELECT 
        m.month,
        m.revenue,
        m.active_customers,
        COALESCE(c.churned_count, 0) AS churned_count,
        (COALESCE(c.churned_count, 0)::float / NULLIF(m.active_customers, 0)) * 100 AS churn_rate
    FROM monthly_data m
    LEFT JOIN churned_customers c ON m.month = c.month
    ORDER BY m.month
    """
    rows = db.execute_query(query, (CHURN_THRESHOLD_DAYS,))
    result = []
    for row in rows:
        result.append({
            "month": row['month'].isoformat() if row['month'] else None,
            "revenue": float(row['revenue']),
            "churn_rate": round(row['churn_rate'] if row['churn_rate'] is not None else 0, 2)
        })
    return result