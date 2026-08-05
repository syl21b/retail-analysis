import sys
from pathlib import Path

# Add the parent directory (the one containing 'dashboard') to sys.path
# This is the same as app.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()  # Will look for .env in the current directory and up

import os

from dashboard.config import Config
from dashboard import database
from dashboard.churn_model import train_model

def main():
    print("🔗 Initialising database...")
    if not Config.DATABASE_URL:
        print("❌ DATABASE_URL is not set in .env")
        sys.exit(1)
    database.init_db(Config.DATABASE_URL)
    print("✅ Database initialised.")
    
    print("🧠 Training churn model (this may take a few minutes)...")
    success = train_model()
    
    if success:
        print("✅ Model trained successfully. Files saved:")
        print("   - churn_model.pkl")
        print("   - scaler.pkl")
        print("\n📦 Please commit these two .pkl files to your repository.")
    else:
        print("❌ Training failed. Check the logs above.")

if __name__ == "__main__":
    main()