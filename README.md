```markdown
# Enterprise BI Dashboard – AI‑Powered Retail Analytics

## 1. Project Overview

This project delivers a **production‑ready, interactive Business Intelligence dashboard** for retail analytics. It processes millions of records from a PostgreSQL database (Neon) and provides:

- **Cross‑filtering charts** – click any bar, pie slice, or drag on the daily revenue chart to filter the entire dashboard.
- **Natural Language Query (NLQ)** – ask business questions in plain English; the AI generates and executes SQL safely.
- **AI Business Analyst** – choose from three personas (Balanced Analyst, Conservative CFO, Growth CMO) to get deep, data‑driven reports.
- **What‑If Simulator** – adjust levers (Repeat Rate, AOV, Churn, Fulfillment Days) and see estimated revenue uplift using a trained linear regression model.
- **Advanced analytics** – CLV, RFM segmentation, cohort retention, revenue anomalies, high‑risk customers, and order status distribution.
- **Security** – JWT authentication, rate limiting, environment‑based configuration, and secure database connection pooling.
- **Export** – AI insights can be exported as PDF or PowerPoint.

---

## 2. Tech Stack

| Layer          | Technologies |
|----------------|--------------|
| **Backend**    | Flask, Python 3.11, Gunicorn |
| **Database**   | PostgreSQL (Neon) with connection pooling |
| **Frontend**   | HTML5, CSS3, JavaScript, Plotly.js |
| **AI / ML**    | Google Gemini / Groq (Llama) – fallback to local analysis, scikit‑learn LinearRegression |
| **Security**   | JWT, rate limiting, secure headers, environment variables |
| **Caching**    | TTLCache (in‑memory) |
| **Export**     | WeasyPrint (PDF), python‑pptx (PowerPoint) |

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

### 3.9 Security & Development Mode
- JWT authentication (production) or disabled for local development (`DISABLE_AUTH=true`).
- Rate limiting per endpoint (AI, NLQ, simulation).
- Security headers (X‑Frame‑Options, HSTS, X‑Content‑Type‑Options, etc.).
- CORS restricted to allowed origins.

### 3.10 Export
- AI insights can be exported as **PDF** (WeasyPrint) or **PowerPoint** (python‑pptx).

---

## 4. Getting Started

### 4.1 Prerequisites
- Python 3.9+
- PostgreSQL database (Neon, AWS RDS, or local) with the `warehouse` schema and the following tables:
  - `fact_orders`, `dim_customers`, `dim_products`, `dim_location`, `dim_payment`, `dim_status`, `dim_time`
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

**5. Prepare SQL queries**
Place your analytics SQL files inside the folder:  
`sql/analytics/` (the exact names must match the mapping in `DataLoader.friendly_data`).  
If you don’t have the SQL files, the app will fall back to loading CSV files from `analytics_results/`.

**6. Run the application**
```bash
python app.py
```
Open `http://localhost:5001` in your browser.

---

## 5. Project Structure

```
.
├── app.py                     # Main Flask application
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not committed)
├── .env.example               # Template for environment variables
├── .gitignore                 # Files/folders to exclude from Git
├── README.md                  # This file
├── templates/
│   └── index.html             # Frontend dashboard (HTML/CSS/JS)
├── sql/
│   └── analytics/             # SQL query files (optional)
└── analytics_results/         # CSV fallback data (optional)
```

---

## 6. Authentication (Production)

By default, the API endpoints are protected by JWT. To obtain a token:

1. Generate an API key (run once, store securely):
   ```python
   from app import auth_manager
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

The AI generates SQL using the `warehouse` schema description (retrieved from the database).

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

- Monthly aggregates are computed from `fact_orders` and `dim_time`.
- Percentage changes in revenue are regressed against percentage changes in:
  - Repeat Rate
  - AOV
  - Churn Rate (derived from repeat rate)
- Coefficients are updated by calling `POST /api/simulate/train` (admin only).
- The simulation endpoint uses the most recent coefficients to estimate revenue uplift.

---

## 10. Maintenance & Customisation

- **Adding new charts** – extend the `pages` object in `index.html` and add corresponding API routes in `app.py`.
- **Modifying personas** – edit `PERSONA_TEMPLATES` in `app.py`.
- **Updating the AI model** – adjust the training logic inside `train_simulation_model()`.

---

## 11. Export

- Click **“Export as PDF”** – the AI insights modal HTML is rendered to PDF (requires WeasyPrint).
- Click **“Export to PowerPoint”** – the AI insights text is placed into a bullet slide (requires python‑pptx).

---

## 12. Testing

No formal test suite is provided yet. You can manually test via:

- `curl` commands for API endpoints.
- Browser interaction for the frontend.

Example:
```bash
curl -H "Authorization: Bearer <token>" http://localhost:5001/api/kpis
```

---

## 13. Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

## 14. License

MIT

---

## 15. Acknowledgements

- Plotly for interactive visualisations.
- Google Gemini and Groq for AI generation.
- Neon for managed PostgreSQL.
- All open‑source libraries used.

---

## 16. Contact

For questions or support, please open an issue on GitHub.
``` 