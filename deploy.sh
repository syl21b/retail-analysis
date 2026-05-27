# deploy.sh
#!/bin/bash

echo "🚀 Starting Retail Analytics Deployment"

# Step 1: Pull latest code
git pull origin main

# Step 2: Install/update dependencies
pip install -r requirements.txt

# Step 3: Run initial pipeline (if first time)
if [ ! -f ".pipeline_completed" ]; then
    echo "📊 Running initial ETL pipeline..."
    python run_full_pipeline.py
    touch .pipeline_completed
fi

# Step 4: Start services with Docker
docker-compose up -d --build

# Step 5: Setup scheduled pipeline (Airflow or cron)
airflow dags trigger retail_etl_dag

echo "✅ Deployment Complete!"
echo "📊 Dashboard: http://localhost:8501"
echo "🔌 API: http://localhost:8000/docs"
echo "📈 Airflow: http://localhost:8080"