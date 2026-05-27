# 1. Create directory structure
mkdir -p retail-analytics/{config,dashboard,data/cleaned,airflow/dags,sql}
cd retail-analytics

# 2. Create requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.28.1
pandas==2.1.3
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
plotly==5.18.0
faker==20.1.0
python-dotenv==1.0.0
EOF

# 3. Run the pipeline locally first
python run_etl_pipeline.py

# 4. Test API locally
uvicorn dashboard.api:app --reload

# 5. Test Dashboard locally
streamlit run dashboard/app.py

# 6. Push to GitHub
git init
git add .
git commit -m "Initial retail analytics pipeline"
git remote add origin https://github.com/yourusername/retail-analytics.git
git push -u origin main

# 7. Deploy to Render
# - Go to render.com
# - Click "New +"
# - Select "Blueprint" (uses render.yaml)
# - Connect your GitHub repo
# - Deploy!
