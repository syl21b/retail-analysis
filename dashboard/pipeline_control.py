import streamlit as st
import subprocess
import json
import pandas as pd
import psycopg2

st.set_page_config(page_title="Retail Analytics", layout="wide")

st.title("🛍️ Retail Analytics Dashboard")

# Sidebar for pipeline control
with st.sidebar:
    st.header("Pipeline Control")
    
    if st.button("🔄 Run Full Pipeline"):
        with st.spinner("Running pipeline..."):
            result = subprocess.run(['python', 'simple_pipeline.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                st.success("✅ Pipeline completed successfully!")
            else:
                st.error(f"❌ Pipeline failed: {result.stderr}")
    
    # Show pipeline status
    try:
        with open('pipeline_status.json', 'r') as f:
            status = json.load(f)
        st.info(f"Last run: {status['timestamp']}")
        st.info(f"Status: {status['status']}")
    except:
        st.warning("No pipeline status found")

# Main content
tab1, tab2, tab3 = st.tabs(["📊 Core Metrics", "👥 Customers", "🏷️ Products"])

with tab1:
    st.header("Key Performance Indicators")
    # Query your analytics views
    # conn = psycopg2.connect(...)
    # df = pd.read_sql("SELECT * FROM v_core_metrics", conn)
    # st.dataframe(df)