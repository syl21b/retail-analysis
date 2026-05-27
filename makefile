# Makefile
.PHONY: help setup pipeline run-api run-dashboard docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make setup        - Install dependencies"
	@echo "  make pipeline     - Run full ETL pipeline"
	@echo "  make run-api      - Start FastAPI backend"
	@echo "  make run-dashboard- Start Streamlit dashboard"
	@echo "  make docker-up    - Start all services with Docker"
	@echo "  make docker-down  - Stop all services"

setup:
	pip install -r requirements.txt

pipeline:
	python run_full_pipeline.py

run-api:
	uvicorn dashboard.api:app --reload --port 8000

run-dashboard:
	streamlit run dashboard/app.py

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# For production deployment with scheduling
schedule-pipeline:
	@echo "Setting up cron job for daily pipeline at 2 AM"
	(crontab -l 2>/dev/null; echo "0 2 * * * cd $(PWD) && python run_full_pipeline.py >> logs/pipeline.log 2>&1") | crontab -