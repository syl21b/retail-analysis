# dashboard/api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any
import os
from datetime import datetime, timedelta

app = FastAPI(title="Retail Analytics API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pool (simplified - use async pool for production)
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'retail_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'password'),
        port=os.getenv('DB_PORT', '5432'),
        cursor_factory=RealDictCursor
    )

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/metrics/core")
async def get_core_metrics():
    """Get core business metrics"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM analytics.core_metrics 
            WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY metric_date DESC
        """)
        results = cur.fetchall()
        return {"metrics": results}
    finally:
        conn.close()

@app.get("/api/metrics/rfm")
async def get_rfm_segmentation():
    """Get RFM customer segmentation"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT segment, customer_count, avg_monetary, avg_frequency, avg_recency
            FROM analytics.rfm_segments
            ORDER BY 
                CASE segment
                    WHEN 'Champions' THEN 1
                    WHEN 'Loyal Customers' THEN 2
                    WHEN 'Potential Loyalists' THEN 3
                    ELSE 4
                END
        """)
        return {"segments": cur.fetchall()}
    finally:
        conn.close()

@app.get("/api/cohort/retention")
async def get_cohort_retention():
    """Get cohort retention metrics"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT cohort_month, period_number, retention_rate, customer_count
            FROM analytics.cohort_retention
            ORDER BY cohort_month DESC, period_number
        """)
        return {"cohort_data": cur.fetchall()}
    finally:
        conn.close()

@app.get("/api/products/top")
async def get_top_products(limit: int = 10, metric: str = "revenue"):
    """Get top performing products"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        query = f"""
            SELECT product_name, category, {metric} as value
            FROM analytics.product_performance
            ORDER BY {metric} DESC
            LIMIT %s
        """
        cur.execute(query, (limit,))
        return {"products": cur.fetchall()}
    finally:
        conn.close()

@app.get("/api/customers/churn-risk")
async def get_churn_risk():
    """Get customers at risk of churning"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT customer_id, name, churn_probability, risk_category, days_since_last_order
            FROM analytics.churn_risk_customers
            WHERE churn_probability > 0.5
            ORDER BY churn_probability DESC
            LIMIT 100
        """)
        return {"at_risk_customers": cur.fetchall()}
    finally:
        conn.close()

@app.post("/api/pipeline/run")
async def trigger_pipeline():
    """Manually trigger ETL pipeline"""
    # Could trigger Airflow DAG or run pipeline asynchronously
    return {"message": "Pipeline triggered", "status": "running"}