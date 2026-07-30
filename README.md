
# Enterprise BI Dashboard – AI‑Powered Retail Analytics

## 1. Project Overview

This project delivers a **production‑ready, interactive Business Intelligence dashboard** for retail analytics. It processes millions of records from a PostgreSQL database and provides:

- **Cross‑filtering charts** – click any bar, pie slice, or drag on the daily revenue chart to filter the entire dashboard.
- **Natural Language Query (NLQ)** – ask business questions in plain English; the AI generates and executes SQL safely.
- **AI Business Analyst** – choose from three personas (Balanced Analyst, Conservative CFO, Growth CMO) to get deep, data‑driven reports.
- **What‑If Simulator** – adjust levers (Repeat Rate, AOV, Churn, Fulfillment Days) and see estimated revenue uplift using a trained linear regression model.
- **Customer Churn Prediction** – real‑time risk scoring using a Random Forest classifier, with adjustable churn threshold and row limits.
- **Advanced analytics** – CLV, RFM segmentation, cohort retention, revenue anomalies, high‑risk customers, and order status distribution.
- **Security** – JWT authentication, rate limiting, environment‑based configuration, and secure database connection pooling.
- **Export** – AI insights can be exported as PDF.

---

## 2. Tech Stack

| Layer          | Technologies |
|----------------|--------------|
| **Backend**    | Flask, Python 3.11+, Gunicorn |
| **Database**   | PostgreSQL (Neon) with connection pooling |
| **Frontend**   | HTML5, CSS3, JavaScript, Plotly.js |
| **AI / ML**    | Google Gemini / Groq (Llama) – fallback to local analysis, scikit‑learn (RandomForest, LinearRegression), joblib for model persistence |
| **Security**   | JWT, rate limiting, secure headers, environment variables |
| **Caching**    | TTLCache (in‑memory) |
| **Export**     | WeasyPrint (PDF) |

---

## 3. Key Features

### 3.1 Interactive Executive Dashboard
- Real‑time KPIs: Total Revenue, Orders, Customers, Average Order Value.
- Daily revenue chart with anomaly detection (highlighting days >20% drop).
- Monthly revenue bar chart.
- Top cities, revenue by category (pie), top subcategories, repeat vs one‑time customers, order status, payment method analysis.

### 3.2 Revenue Analytics
- Daily / monthly trends.
- Pareto chart (revenue concentration) and top customers by revenue.
- Order value distribution (min, max, median).

### 3.3 Customer Intelligence
- Highest and lowest CLV customers.
- Repeat vs one‑time breakdown.
- Customer segmentation (Bronze, Silver, Gold, Platinum).
- High‑risk VIP customers (RFM‑based).

### 3.4 Product Performance
- Revenue by category and subcategory – click category to drill down.
- AOV and purchase frequency per category.

### 3.5 RFM Segmentation & Cohort Retention
- Recency / Frequency / Monetary scatter plot.
- Segment distribution pie chart.
- Cohort retention heatmap and retention curves.

### 3.6 Natural Language Query (NLQ)
- Write questions like *“show me top 5 customers by revenue in March”*.
- AI generates PostgreSQL SELECT statements (schema‑aware).
- Results are cached for repeated questions.

### 3.7 AI Business Analyst
- Three personas: **Balanced Analyst**, **Conservative CFO**, **Growth CMO**.
- Generates a report with sections: Executive Summary, Key Metrics, Deep Dive, Root Causes, Actionable Recommendations, Expected Business Impact.
- Uses live data (KPIs, daily/monthly revenue, top cities/categories, repeat rate, CLV, RFM, cohorts, anomalies, high‑risk customers, order status).

### 3.8 What‑If Simulator
- Modify business levers: Repeat Rate (percentage points), AOV (%), Churn Rate (%), Fulfillment Days (days).
- Model is trained monthly from historical data (linear regression).
- Instantly displays estimated revenue uplift and new total revenue.

### 3.9 Customer Churn Prediction
- **Machine learning model**: Random Forest Classifier trained on customer features: recency, frequency, monetary value, tenure, average days between orders, average order value.
- **Adjustable threshold**: Users can select a churn window (30, 60, 90, 120, 180, 365 days) – the model retrains dynamically.
- **At‑risk list**: View customers with the highest churn probability (limited by row count).
- **Individual prediction**: Enter a customer ID to get a personalised churn probability and risk level (High / Medium / Low).
- **Visualisation**: Risk distribution pie chart (High / Medium / Low) and a timeline chart showing monthly revenue versus churn rate.
- **Model persistence**: The trained model is saved to disk (`churn_model.pkl`, `scaler.pkl`) and reloaded on startup.

### 3.10 Security & Development Mode
- JWT authentication (production) or disabled for local development (`DISABLE_AUTH=true`).
- Rate limiting per endpoint (AI, NLQ, simulation).
- Security headers (X‑Frame‑Options, HSTS, X‑Content‑Type‑Options, etc.).
- CORS restricted to allowed origins.

### 3.11 Export
- AI insights can be exported as **PDF** (WeasyPrint).

---

## 4. Getting Started

### 4.1 Prerequisites
- Python 3.11+
- PostgreSQL database (Neon, AWS RDS, or local) with the `public` schema and the following tables:
  - `fact_orders` (columns: `order_id`, `customer_id`, `order_date`, `net_amount`, `product_id`, `category`, `subcategory`, `city`, `payment_method`, `order_status`)
- (Optional) API keys for Gemini or Groq – if not provided, a local fallback analysis runs.

### 4.2 Installation

**1. Clone the repository**
```bash
git clone https://github.com/your-username/enterprise-bi-dashboard.git
cd enterprise-bi-dashboard
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**
Copy `.env.example` to `.env` and fill in your details:
```bash
cp .env.example .env
```
Edit `.env` with your database URL, secret key, AI keys (optional), and CORS settings.

**For local development**, set `DISABLE_AUTH=true` to skip JWT authentication.

**5. Prepare SQL queries (optional)**
Place your analytics SQL files inside the folder:  
`sql/analytics/` (the exact names must match the mapping in `DataLoader.friendly_data`).  
If you don’t have the SQL files, the app will try to load CSV data from `analytics_results/`.

**6. Run the application**

The application is structured as a Python package (`dashboard/`). To run it:

```bash
# Using Flask development server
python -m dashboard.app

# Using Gunicorn (production)
gunicorn dashboard.app:app --bind 0.0.0.0:5001
```

Open `http://localhost:5001` in your browser.

---

## 5. Project Structure

```
.
├── dashboard/                  # Main package
│   ├── __init__.py             # Package marker
│   ├── app.py                  # Flask application factory & entry point
│   ├── config.py               # Configuration (environment variables)
│   ├── database.py             # Database connection pool & queries
│   ├── auth.py                 # JWT, rate limiting, authentication
│   ├── routes.py               # All API endpoints
│   ├── data_loader.py          # SQL file loader / CSV fallback
│   ├── sql_helpers.py          # SQL sanitisation, schema prefix, index creation
│   ├── ai.py                   # AI persona templates, multi‑provider AI calls
│   ├── simulation.py           # What‑if simulation model training & logic
│   ├── churn_model.py          # Churn prediction (Random Forest)
│   ├── export.py               # PDF generation
│   └── templates/
│       └── index.html          # Frontend dashboard (HTML/CSS/JS)
├── sql/
│   └── analytics/              # SQL query files (optional)
├── analytics_results/          # CSV fallback data (optional)
├── requirements.txt            # Python dependencies
├── .env.example                # Template for environment variables
├── .gitignore                  # Files/folders to exclude from Git
├── render.yaml                 # Render.com deployment configuration
└── README.md                   # This file
```

---

## 6. Authentication (Production)

By default, the API endpoints are protected by JWT. To obtain a token:

1. Generate an API key (run once, store securely):
   ```python
   from dashboard.auth import auth_manager
   print(auth_manager.generate_api_key('admin', 'admin'))
   ```
2. In your frontend, call `POST /api/login` with `{"api_key": "your-key"}`.
3. Use the returned JWT in the `Authorization: Bearer <token>` header for all subsequent requests.

For development, set `DISABLE_AUTH=true` in `.env` – then no token is required.

---

## 7. Example Natural Language Queries

- *“Show me top 5 customers by revenue”*
- *“What was the total revenue in March 2025?”*
- *“List customers who have not placed an order in the last 90 days”*
- *“Which product category has the highest average order value?”*

The AI generates SQL using the `public` schema description (retrieved from the database).

---

## 8. AI Insights (Sample Output)

The AI report includes sections like:

- **Executive Summary** – a 2‑3 sentence overview of business health.
- **Key Metrics & Filters** – current KPIs and any applied filters.
- **Deep Dive** – revenue, retention, and operational analysis.
- **Root Causes** – why certain metrics are underperforming.
- **Actionable Recommendations** – short‑term (30 days) and long‑term (6‑12 months).
- **Expected Business Impact** – quantifiable outcomes.

Personas influence the tone and focus (e.g., CFO emphasises risk, CMO emphasises growth).

---

## 9. What‑If Simulator Logic

- Monthly aggregates are computed from `fact_orders`.
- Percentage changes in revenue are regressed against percentage changes in:
  - Repeat Rate
  - AOV
  - Churn Rate (derived from repeat rate)
- Coefficients are updated by calling `POST /api/simulate/train` (admin only).
- The simulation endpoint uses the most recent coefficients to estimate revenue uplift.

---

## 10. Churn Prediction Model Details

- **Features**: recency (days since last order), frequency (number of orders), monetary (total spend), tenure (days since first order), average days between orders, average order value.
- **Target**: binary label (1 if recency > threshold, else 0).
- **Algorithm**: Random Forest Classifier (balanced class weights, 100 trees).
- **Training**: The model is automatically trained on startup (if no saved model exists) and retrained when the threshold is changed.
- **Persistence**: Saved to `churn_model.pkl` and `scaler.pkl` in the working directory.
- **Endpoint**:
  - `GET /api/churn/stats?threshold=<days>` – returns overall churn statistics and risk distribution.
  - `GET /api/churn/at_risk?limit=<n>&threshold=<days>` – returns the top `n` customers with highest churn probability.
  - `GET /api/churn/predict?customer_id=<id>` – returns churn probability and risk level for a single customer.
  - `POST /api/churn/train` – force retraining (admin only).

---

## 11. Maintenance & Customisation

- **Adding new charts** – extend the `pages` object in `index.html` and add corresponding API routes in `routes.py`.
- **Modifying personas** – edit `PERSONA_TEMPLATES` in `ai.py`.
- **Updating the simulation model** – adjust the training logic inside `simulation.py`.
- **Changing churn model hyperparameters** – edit `churn_model.py` (e.g., `n_estimators`, `max_depth`).
- **Adding new database tables** – update the schema description in `get_schema_description()` and the SQL queries in the `sql/` folder or `data_loader.py`.

---

## 12. Export

- Click **“Download Report PDF”** – the AI insights modal HTML is rendered to PDF (requires WeasyPrint).

---

## 13. Testing

No formal test suite is provided yet. You can manually test via:

- `curl` commands for API endpoints.
- Browser interaction for the frontend.

Example:
```bash
curl -H "Authorization: Bearer <token>" http://localhost:5001/api/kpis
```

---

## 14. Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

## 15. License

MIT

---

## 16. Acknowledgements

- Plotly for interactive visualisations.
- Google Gemini and Groq for AI generation.
- Neon for managed PostgreSQL.
- All open‑source libraries used.

---

## 17. Contact

For questions or support, please open an issue on GitHub.
