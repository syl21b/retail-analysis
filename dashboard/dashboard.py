import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import glob
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Retail Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #667eea;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #7f8c8d;
        margin-top: 0.5rem;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    .insight-text {
        background-color: #f0f9f0;
        padding: 0.75rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    .story-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Load all data
@st.cache_data
def load_all_data():
    """Load all CSV files from analytics_results folder"""
    data = {}
    
    # Find analytics_results folder
    results_paths = [
        Path("analytics_results"),
        Path("../analytics_results"),
        Path("../../analytics_results"),
    ]
    
    results_folder = None
    for path in results_paths:
        if path.exists():
            results_folder = path
            break
    
    if results_folder is None:
        return data
    
    # Load all CSV files
    csv_files = glob.glob(str(results_folder / "*.csv"))
    
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            name = Path(file).stem
            data[name] = df
        except Exception as e:
            st.warning(f"Could not load {Path(file).name}: {e}")
    
    return data

# Load data
data = load_all_data()

if not data:
    st.error("❌ No data found! Please run run_analytics_queries.py first.")
    st.stop()

# Map files to friendly names
file_mapping = {
    '1a_Customer_Lifetime_Value__CLV_': 'Customer Lifetime Value',
    '1b_Daily_Revenue_Trends': 'Daily Revenue Trends',
    '1c_Monthly_Revenue_Trends': 'Monthly Revenue Trends',
    '1d_Top_Cities_by_Revenue': 'Top Cities by Revenue',
    '2a_Order_Fulfillment_Performance': 'Order Fulfillment Performance',
    '2b_Order_Status_Distribution': 'Order Status Distribution',
    '2c_Revenue_by_Payment_Method': 'Revenue by Payment Method',
    '2d_Repeat_vs_One-Time_Customers': 'Repeat vs One-Time Customers',
    '3a_Cohort_Analysis__Customer_Retention_Over_Time_': 'Cohort Analysis',
    '3b_Customer_Segmentation_using_Revenue___Behavior': 'Customer Segmentation',
    '3c_Order_Value_Distribution___Basket_Analysis': 'Order Value Distribution',
    '3d_Revenue_Contribution_Analysis': 'Revenue Contribution Analysis',
    '3e_Time-to-Purchase_Behavior': 'Time to Purchase Behavior',
    '4_RFM_Segmentation': 'RFM Segmentation',
    '5_Cohort_Retention_Analysis': 'Cohort Retention Analysis',
    '6_Churn_Detection': 'Churn Detection',
    '7_Revenue_by_Product_Category': 'Revenue by Product Category',
    '8_Revenue_by_Location': 'Revenue by Location',
    '9_Payment_Method_Analysis': 'Payment Method Analysis',
    '10_Order_Status_Analysis': 'Order Status Analysis'
}

# Create friendly data dictionary
friendly_data = {}
for key, value in file_mapping.items():
    if key in data:
        friendly_data[value] = data[key]

st.markdown("""
<div class="main-header">
    <h1>📊 Retail Analytics Dashboard</h1>
    <p>Complete Business Intelligence Platform</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 📊 Navigation")
    
    pages = {
        "🏠 Overview": "overview",
        "💰 Revenue Analytics": "revenue",
        "👥 Customer Analytics": "customers",
        "📦 Order Analytics": "orders",
        "🏷️ Product Analytics": "products",
        "🌍 Geographic Analytics": "geo",
        "⭐ RFM & Segmentation": "rfm",
        "📈 Cohort & Retention": "cohort",
        "📊 Data Explorer": "explorer"
    }
    
    selected_page = st.radio("Select Section", list(pages.keys()))
    
    st.markdown("---")
    st.markdown("### 📁 Available Data")
    st.metric("Total Datasets", len(friendly_data))
    
    with st.expander("View All Datasets"):
        for name in friendly_data.keys():
            st.caption(f"• {name}")

# ==================== OVERVIEW PAGE ====================
if selected_page == "🏠 Overview":
    st.markdown('<div class="section-header">🎯 Key Performance Indicators</div>', unsafe_allow_html=True)
    
    # Calculate KPIs
    total_revenue = 0
    if 'Revenue Contribution Analysis' in friendly_data:
        df = friendly_data['Revenue Contribution Analysis']
        total_revenue = df['total_revenue'].sum()
    
    total_orders = 0
    if 'Order Status Distribution' in friendly_data:
        df = friendly_data['Order Status Distribution']
        total_orders = df['order_count'].sum()
    
    total_customers = 0
    if 'Customer Segmentation' in friendly_data:
        df = friendly_data['Customer Segmentation']
        total_customers = len(df['customer_id'].unique())
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${total_revenue:,.0f}</div>
            <div class="metric-label">💰 Total Revenue</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_orders:,}</div>
            <div class="metric-label">📦 Total Orders</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_customers:,}</div>
            <div class="metric-label">👥 Total Customers</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        avg_order = total_revenue / total_orders if total_orders > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${avg_order:,.0f}</div>
            <div class="metric-label">📊 Avg Order Value</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Business story for Overview
    st.markdown("""
    <div class="info-box">
        <strong>📖 The Big Picture – What This Dashboard Solves</strong><br>
        As a retail business, you need a single source of truth to understand <strong>financial health, customer behavior, and operational efficiency</strong>.
        The KPIs above show your overall performance. But the real story lies in the trends and breakdowns below – they help answer:
        <ul>
            <li>Is revenue growing consistently or seasonally?</li>
            <li>Which cities and product categories drive most sales?</li>
            <li>Are we at risk of losing customers?</li>
        </ul>
        The following charts are <strong>interconnected</strong> – note how daily fluctuations may relate to product or geographic performance.
    </div>
    """, unsafe_allow_html=True)
    
    # Revenue Trends
    st.markdown('<div class="section-header">📈 Revenue Trends – The Growth Narrative</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        if 'Daily Revenue Trends' in friendly_data:
            df = friendly_data['Daily Revenue Trends']
            fig = px.line(df, x='order_day', y='total_amount', 
                         title='Daily Revenue Trends',
                         labels={'order_day': 'Date', 'total_amount': 'Revenue ($)'})
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("🔍 *Daily volatility reveals short-term campaign impacts or seasonality.*")
    
    with col2:
        if 'Monthly Revenue Trends' in friendly_data:
            df = friendly_data['Monthly Revenue Trends']
            fig = px.bar(df, x='year_month', y='total_amount',
                        title='Monthly Revenue Trends',
                        labels={'year_month': 'Month', 'total_amount': 'Revenue ($)'})
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("📆 *Monthly view smooths out noise – look for upward/downward trends.*")
    
    st.markdown("""
    <div class="insight-text">
        💡 <strong>Business Insight:</strong> Compare the daily and monthly charts. 
        A rising monthly trend with high daily fluctuations may indicate successful promotions on specific days. 
        Flat or declining monthly revenue signals a need to revisit pricing, marketing, or product mix.
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Insights
    st.markdown('<div class="section-header">🔍 Quick Insights – Where to Focus</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        if 'Top Cities by Revenue' in friendly_data:
            df = friendly_data['Top Cities by Revenue']
            fig = px.bar(df.head(5), x='city', y='total_revenue',
                        title='Top 5 Cities by Revenue')
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("📍 *Geographic concentration – top cities may need localised marketing.*")
    
    with col2:
        if 'Revenue by Product Category' in friendly_data:
            df = friendly_data['Revenue by Product Category']
            fig = px.pie(df, values='revenue', names='category',
                        title='Revenue by Product Category', hole=0.3)
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("🏷️ *Product mix – which categories are cash cows vs. underperformers.*")
    
    st.markdown("""
    <div class="insight-text">
        🎯 <strong>Actionable Recommendation:</strong> 
        If 2-3 cities generate >60% of revenue, consider geographic expansion or protect those markets with loyalty programs. 
        Similarly, if one product category dominates revenue, diversification may reduce risk.
    </div>
    """, unsafe_allow_html=True)

# ==================== REVENUE ANALYTICS ====================
elif selected_page == "💰 Revenue Analytics":
    st.markdown('<div class="section-header">💰 Revenue Analytics – The Money Story</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>📖 Business Problem:</strong> "Why is revenue not growing as expected? Where is the leakage?"<br>
        This page dissects revenue from every angle: <strong>trends, concentration (Pareto), customer contribution, and order value distribution</strong>.
        The charts are connected – a drop in daily revenue might be explained by a shift in order value or a few top customers reducing spend.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if 'Daily Revenue Trends' in friendly_data:
            df = friendly_data['Daily Revenue Trends']
            fig = px.line(df, x='order_day', y='total_amount', 
                         title='Daily Revenue Trends',
                         labels={'order_day': 'Date', 'total_amount': 'Revenue ($)'})
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if 'Monthly Revenue Trends' in friendly_data:
            df = friendly_data['Monthly Revenue Trends']
            fig = px.bar(df, x='year_month', y='total_amount',
                        title='Monthly Revenue Trends',
                        labels={'year_month': 'Month', 'total_amount': 'Revenue ($)'})
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div class="insight-text">
        🔗 <strong>Connected Story:</strong> 
        If daily revenue is spiking but monthly is flat, it suggests short-lived promotions. 
        Use monthly trends to set realistic targets; daily to optimise campaign timing.
    </div>
    """, unsafe_allow_html=True)
    
    # Revenue Contribution
    if 'Revenue Contribution Analysis' in friendly_data:
          st.markdown('<div class="section-header">📊 Who Drives Your Revenue? (Pareto Analysis)</div>', unsafe_allow_html=True)
          df = friendly_data['Revenue Contribution Analysis']
          
          col1, col2 = st.columns(2)
          with col1:
               # Prepare top 10 customers
               top_customers = df.nlargest(10, 'total_revenue')[['customer_id', 'total_revenue']].copy()
               # Add full_name if available, otherwise create a readable label
               if 'full_name' in df.columns:
                    top_customers = top_customers.merge(df[['customer_id', 'full_name']], on='customer_id', how='left')
                    top_customers['label'] = top_customers['full_name']
               else:
                    top_customers['label'] = 'ID: ' + top_customers['customer_id'].astype(str)
               
               top_customers['total_revenue_formatted'] = top_customers['total_revenue'].apply(lambda x: f"${x:,.0f}")
               
               fig = go.Figure(data=[
                    go.Bar(
                         x=top_customers['label'],
                         y=top_customers['total_revenue'],
                         text=top_customers['total_revenue_formatted'],
                         textposition='outside',
                         marker_color='#667eea',
                         hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.0f}<br>Customer ID: %{customdata}<extra></extra>',
                         customdata=top_customers['customer_id'].astype(str)
                    )
               ])
               fig.update_layout(
                    title='Top 10 Customers by Revenue',
                    xaxis_title='Customer Name',
                    yaxis_title='Revenue ($)',
                    height=450,
                    xaxis_tickangle=-45
               )
               st.plotly_chart(fig, use_container_width=True)
          with col2:
               df_display = df.head(100).copy()
               df_display['cumulative_percentage_display'] = df_display['cumulative_percentage'] * 100
               fig = go.Figure()
               fig.add_trace(go.Scatter(x=df_display.index, y=df_display['cumulative_percentage_display'],
                                        mode='lines', name='Cumulative Revenue %',
                                        line=dict(color='#667eea', width=3), fill='tozeroy',
                                        fillcolor='rgba(102, 126, 234, 0.2)'))
               fig.add_hline(y=80, line_dash="dash", line_color="red", 
                              annotation_text="80% Pareto Line", annotation_position="top right")
               fig.update_layout(title='Revenue Concentration (Pareto Analysis)',
                                   xaxis_title='Customer Rank', yaxis_title='Cumulative Revenue (%)',
                                   height=450, yaxis_range=[0, 100])
               st.plotly_chart(fig, use_container_width=True)
          
          st.markdown("""
          <div class="insight-text">
               📌 <strong>Key Insight:</strong> If the top 10 customers represent more than 50% of revenue, your business is highly dependent on a few clients. 
               This is risky. The Pareto chart shows the exact percentage – aim to diversify your customer base.
          </div>
          """, unsafe_allow_html=True)
    
    # Order Value Distribution
    if 'Order Value Distribution' in friendly_data:
        st.markdown('<div class="section-header">💰 Order Value Analysis – Ticket Size Matters</div>', unsafe_allow_html=True)
        df = friendly_data['Order Value Distribution']
        metrics_cols = st.columns(4)
        for i, col in enumerate(['max_order_value', 'min_order_value', 'avg_order_value', 'median_order_value']):
            with metrics_cols[i]:
                st.metric(col.replace('_', ' ').title(), f"${df[col].iloc[0]:,.2f}")
        st.markdown("""
        <div class="insight-text">
            💡 <strong>Business Action:</strong> 
            A large gap between average and median indicates outliers. If median is low, focus on upselling or bundling to increase basket size. 
            Compare with daily revenue – a drop in order value may explain revenue decline even if order count is stable.
        </div>
        """, unsafe_allow_html=True)

# ==================== CUSTOMER ANALYTICS ====================
elif selected_page == "👥 Customer Analytics":
    st.markdown('<div class="section-header">👥 Customer Analytics – Understanding Who Stays & Who Leaves</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>📖 Business Problem:</strong> "Why are we losing customers? Which customers are most valuable?"<br>
        This page connects <strong>Customer Lifetime Value (CLV)</strong>, <strong>repeat vs. one-time buyers</strong>, 
        <strong>segmentation</strong>, and <strong>churn risk</strong>. The story flows from identifying your best customers 
        to diagnosing why others stop buying.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if 'Customer Lifetime Value' in friendly_data:
            df = friendly_data['Customer Lifetime Value']
            highest = df[df['category'] == 'Highest']
            highest['total_net_amount_formatted'] = highest['total_net_amount'].apply(lambda x: f"${x:,.0f}")
            fig = go.Figure(data=[
                go.Bar(x=highest['full_name'], y=highest['total_net_amount'],
                       text=highest['total_net_amount_formatted'], textposition='outside',
                       marker_color='#667eea')
            ])
            fig.update_layout(title='Top 5 Customers by Lifetime Value', xaxis_title='Customer',
                              yaxis_title='Value ($)', height=450, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("👑 *These are your VIPs – losing them would hurt revenue significantly.*")
    with col2:
        if 'Repeat vs One-Time Customers' in friendly_data:
            df = friendly_data['Repeat vs One-Time Customers']
            fig = px.pie(df, values='customer_count', names='customer_type',
                        title='Customer Type Distribution', hole=0.3)
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("🔄 *A high proportion of one-time buyers indicates low loyalty.*")
    
    st.markdown("""
    <div class="insight-text">
        🔗 <strong>Connection:</strong> 
        The CLV chart shows who your best customers are. The repeat/one-time pie tells you if you're converting first-timers into repeat buyers. 
        If CLV is driven by only a few customers <strong>and</strong> most customers are one-time, your business has a retention problem.
    </div>
    """, unsafe_allow_html=True)
    
    # Customer Segmentation
    if 'Customer Segmentation' in friendly_data:
        st.markdown('<div class="section-header">🏷️ Customer Segmentation – Tailored Strategies</div>', unsafe_allow_html=True)
        df = friendly_data['Customer Segmentation']
        df['Segment'] = pd.qcut(df['total_revenue'], q=4, labels=['Bronze', 'Silver', 'Gold', 'Platinum'])
        segment_counts = df['Segment'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(values=segment_counts.values, names=segment_counts.index,
                        title='Customer Segments', hole=0.3)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.box(df, x='Segment', y='total_revenue',
                        title='Revenue Distribution by Segment')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("""
        <div class="insight-text">
            🎯 <strong>Strategy:</strong> 
            Use segments to personalise marketing. Platinum customers get VIP perks; Bronze customers receive win-back offers. 
            The box plot shows revenue spread – if Bronze has a wide range, some may be ready to upgrade with the right incentive.
        </div>
        """, unsafe_allow_html=True)
    
    # Churn Detection
    if 'Churn Detection' in friendly_data:
        st.markdown('<div class="section-header">⚠️ Churn Analysis – The Silent Revenue Killer</div>', unsafe_allow_html=True)
        df = friendly_data['Churn Detection']
        churn_counts = df['churn_status'].value_counts()
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(values=churn_counts.values, names=churn_counts.index,
                        title='Customer Churn Status', hole=0.3)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=df['days_since_last_order'], nbinsx=20,
                                       marker_color='#667eea', opacity=0.7))
            fig.update_layout(title='Days Since Last Order Distribution',
                              xaxis_title='Days Since Last Order', yaxis_title='Number of Customers',
                              height=400, bargap=0.05)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("""
        <div class="insight-text">
            ⚠️ <strong>Immediate Action:</strong> 
            If churn rate is >20%, investigate why. The histogram shows how many customers are "dormant". 
            Combine with segmentation – are Platinum customers churning? That's a crisis. Launch reactivation campaigns for those with 30-60 days of inactivity.
        </div>
        """, unsafe_allow_html=True)

# ==================== ORDER ANALYTICS ====================
elif selected_page == "📦 Order Analytics":
    st.markdown('<div class="section-header">📦 Order Analytics – Operational Health & Customer Experience</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>📖 Business Problem:</strong> "Are we fulfilling orders efficiently? Which payment methods drive revenue?"<br>
        This page connects <strong>order status</strong>, <strong>payment methods</strong>, <strong>fulfillment gaps</strong>, and <strong>time to repurchase</strong>.
        The story reveals friction points that may cause cart abandonment or churn.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if 'Order Status Distribution' in friendly_data:
            df = friendly_data['Order Status Distribution']
            fig = px.pie(df, values='order_count', names='order_status',
                        title='Order Status Distribution', hole=0.3)
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if 'Payment Method Analysis' in friendly_data:
            df = friendly_data['Payment Method Analysis']
            fig = px.bar(df, x='payment_method', y='revenue',
                        title='Revenue by Payment Method',
                        labels={'payment_method': 'Payment Method', 'revenue': 'Revenue ($)'})
            fig.update_layout(height=450, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div class="insight-text">
        🔗 <strong>Connection:</strong> 
        If a large share of orders is 'pending' or 'cancelled', check if those customers predominantly use a specific payment method 
        that may be failing. Optimise checkout for the top revenue-generating methods.
    </div>
    """, unsafe_allow_html=True)
    
    # Order Fulfillment
    if 'Order Fulfillment Performance' in friendly_data:
        st.markdown('<div class="section-header">🚚 Fulfillment Gaps – Are We Losing Customers to Slow Delivery?</div>', unsafe_allow_html=True)
        df = friendly_data['Order Fulfillment Performance']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Customers", f"{df['total_customers'].iloc[0]:,}")
        with col2:
            st.metric("Customers Over 30 Days", f"{df['customers_over_30d'].iloc[0]:,}")
        with col3:
            st.metric("Long Gap Percentage", f"{df['customers_with_long_gaps_pct'].iloc[0]}%")
        st.markdown("""
        <div class="insight-text">
            🚨 <strong>Red Flag:</strong> 
            A high percentage of customers with >30 days between orders suggests operational delays or poor post-purchase experience. 
            Cross-reference with churn data – these customers are at high risk.
        </div>
        """, unsafe_allow_html=True)
    
    # Time to Purchase - Excluding <=7 days
    if 'Time to Purchase Behavior' in friendly_data:
        st.markdown('<div class="section-header">⏱️ Time to Purchase – When Do Customers Come Back?</div>', unsafe_allow_html=True)
        df = friendly_data['Time to Purchase Behavior']
        df_filtered = df[df['days_between_orders'] > 7].copy()
        
        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=df_filtered['days_between_orders'], nbinsx=30,
                                       marker_color='#667eea', opacity=0.7))
            fig.update_layout(title='Distribution of Days Between Orders (Excluding ≤7 days)',
                              xaxis_title='Days Between Orders', yaxis_title='Frequency',
                              height=450, bargap=0.05)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = go.Figure()
            fig.add_trace(go.Box(y=df_filtered['days_between_orders'], name='Days Between Orders',
                                 marker_color='#667eea', boxmean='sd'))
            fig.update_layout(title='Statistical Distribution of Days Between Orders',
                              yaxis_title='Days Between Orders', height=450)
            st.plotly_chart(fig, use_container_width=True)
        
        stats_cols = st.columns(4)
        with stats_cols[0]:
            st.metric("Mean Days", f"{df_filtered['days_between_orders'].mean():.1f}")
        with stats_cols[1]:
            st.metric("Median Days", f"{df_filtered['days_between_orders'].median():.0f}")
        with stats_cols[2]:
            st.metric("Std Dev", f"{df_filtered['days_between_orders'].std():.1f}")
        with stats_cols[3]:
            st.metric("Sample Size", f"{len(df_filtered):,}")
        
        st.markdown("""
        <div class="insight-text">
            📅 <strong>Retention Strategy:</strong> 
            If the median time to repurchase is, say, 45 days, send a reminder or discount at day 30. 
            A high standard deviation means inconsistent repurchase behaviour – segment these customers for targeted campaigns.
        </div>
        """, unsafe_allow_html=True)

# ==================== PRODUCT ANALYTICS ====================
elif selected_page == "🏷️ Product Analytics":
    st.markdown('<div class="section-header">🏷️ Product Analytics – What’s Selling & What’s Not</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>📖 Business Problem:</strong> "Which products should we promote or discontinue?"<br>
        This page focuses on <strong>revenue by category</strong>. The story helps prioritise inventory, marketing spend, and pricing strategies.
    </div>
    """, unsafe_allow_html=True)
    
    if 'Revenue by Product Category' in friendly_data:
        df = friendly_data['Revenue by Product Category']
        col1, col2 = st.columns([2, 1])
        with col1:
            df['revenue_formatted'] = df['revenue'].apply(lambda x: f"${x:,.0f}")
            fig = go.Figure(data=[
                go.Bar(x=df['category'], y=df['revenue'],
                       text=df['revenue_formatted'], textposition='outside',
                       marker_color='#667eea')
            ])
            fig.update_layout(title='Revenue by Product Category', xaxis_title='Category',
                              yaxis_title='Revenue ($)', height=500, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.pie(df, values='revenue', names='category',
                        title='Revenue Share by Category', hole=0.3)
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class="insight-text">
            📦 <strong>Product Mix Recommendations:</strong> 
            - The top 1-2 categories are your core business – ensure stock availability.<br>
            - Low-revenue categories may be candidates for bundling with top sellers or discontinuing.<br>
            - Compare with geographic data: maybe a poor category performs well in certain cities – adjust regional assortments.
        </div>
        """, unsafe_allow_html=True)

# ==================== GEOGRAPHIC ANALYTICS ====================
elif selected_page == "🌍 Geographic Analytics":
    st.markdown('<div class="section-header">🌍 Geographic Analytics – Where to Grow Next</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>📖 Business Problem:</strong> "Should we expand to new cities or double down on current ones?"<br>
        This page shows <strong>revenue by city and state</strong>. The story guides market expansion and localised marketing.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if 'Top Cities by Revenue' in friendly_data:
            df = friendly_data['Top Cities by Revenue']
            df['total_revenue_formatted'] = df['total_revenue'].apply(lambda x: f"${x:,.0f}")
            fig = go.Figure(data=[
                go.Bar(x=df['city'], y=df['total_revenue'],
                       text=df['total_revenue_formatted'], textposition='outside',
                       marker_color='#667eea')
            ])
            fig.update_layout(title='Top Cities by Revenue', xaxis_title='City',
                              yaxis_title='Revenue ($)', height=500, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if 'Revenue by Location' in friendly_data:
            df = friendly_data['Revenue by Location']
            fig = px.pie(df, values='revenue', names='state',
                        title='Revenue by State', hole=0.3)
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div class="insight-text">
        🗺️ <strong>Expansion Strategy:</strong> 
        If one city accounts for >30% of revenue, it’s both an opportunity and a risk. 
        Look at the next top cities – they might be candidates for increased marketing spend. 
        Also compare with product categories: a city that loves high-margin products deserves premium placement.
    </div>
    """, unsafe_allow_html=True)

# ==================== RFM & SEGMENTATION ====================
elif selected_page == "⭐ RFM & Segmentation":
    st.markdown('<div class="section-header">⭐ RFM Segmentation – Your Customer Value Map</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>📖 Business Problem:</strong> "Which customers should we invest in, and which have already churned?"<br>
        RFM (Recency, Frequency, Monetary) is a proven method to segment customers. This page connects the segment distribution 
        with a scatter plot of recency vs. monetary value. The story prioritises customer retention actions.
    </div>
    """, unsafe_allow_html=True)
    
    if 'RFM Segmentation' in friendly_data:
        df = friendly_data['RFM Segmentation']
        col1, col2 = st.columns(2)
        with col1:
            segment_counts = df['segment'].value_counts()
            fig = px.pie(values=segment_counts.values, names=segment_counts.index,
                        title='RFM Segments Distribution', hole=0.3)
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.scatter(df, x='recency_days', y='monetary', 
                            color='segment', size='frequency',
                            title='Recency vs Monetary Value',
                            labels={'recency_days': 'Recency (days)', 'monetary': 'Monetary Value ($)'},
                            hover_data=['full_name'])
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class="insight-text">
            📊 <strong>Segment Interpretation:</strong><br>
            - <strong>Champions</strong> (high recency, high monetary): Reward them with loyalty perks.<br>
            - <strong>At Risk</strong> (high monetary but low recency): Send reactivation offers immediately.<br>
            - <strong>New Customers</strong> (low recency, low monetary): Onboard them with educational content.<br>
            The scatter plot makes these groups visible – hover over points to see individual customers.
        </div>
        """, unsafe_allow_html=True)
        
        # Segment Statistics
        st.markdown("#### Segment Statistics")
        stats = df.groupby('segment').agg({
            'recency_days': 'mean',
            'frequency': 'mean',
            'monetary': 'mean'
        }).round(2)
        stats.columns = ['Avg Recency (days)', 'Avg Frequency', 'Avg Monetary Value ($)']
        st.dataframe(stats, use_container_width=True)
        st.markdown("""
        <div class="insight-text">
            💰 <strong>Action:</strong> 
            Focus your retention budget on segments with high monetary value but deteriorating recency. 
            Compare with churn detection – those segments often overlap.
        </div>
        """, unsafe_allow_html=True)

# ==================== COHORT & RETENTION ====================
elif selected_page == "📈 Cohort & Retention":
    st.markdown('<div class="section-header">📈 Cohort Retention – The Ultimate Loyalty Metric</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>📖 Business Problem:</strong> "Are newer customers less loyal than older ones? Does retention improve over time?"<br>
        Cohort analysis tracks groups of customers who joined in the same month. The heatmap and curves show how retention changes over months. 
        This page tells the story of whether your customer experience is improving.
    </div>
    """, unsafe_allow_html=True)
    
    if 'Cohort Retention Analysis' in friendly_data:
        df = friendly_data['Cohort Retention Analysis']
        df_filtered = df[df['month_number'] > 0].copy()
        pivot_df = df_filtered.pivot_table(index='cohort_month', columns='month_number', values='retention_rate')
        
        fig = px.imshow(pivot_df, 
                       title='Cohort Retention Heatmap (Excluding Month 0)',
                       labels=dict(x="Months Since First Order", y="Cohort Month", color="Retention Rate (%)"),
                       aspect="auto", color_continuous_scale='RdYlGn', text_auto='.1f')
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class="insight-text">
            🔥 <strong>Heatmap Story:</strong> 
            Look at the diagonal – how does each cohort retain at month 1,2,3? 
            If newer cohorts have darker red (lower retention) than older ones, your product/marketing is getting worse. 
            If they are greener, improvements are working.
        </div>
        """, unsafe_allow_html=True)
        
        # Retention curves
        st.markdown("#### Retention Curves by Cohort")
        fig = px.line(df_filtered, x='month_number', y='retention_rate', color='cohort_month',
                     title='Customer Retention by Cohort',
                     labels={'month_number': 'Months Since First Order', 'retention_rate': 'Retention Rate (%)'})
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class="insight-text">
            📉 <strong>Curve Interpretation:</strong> 
            Steep drop from month 0 to month 1 indicates poor onboarding. A flat curve after month 2 suggests a loyal core. 
            Identify the month where retention stabilises – that’s your "habit window". Use campaigns to push customers past that point.
        </div>
        """, unsafe_allow_html=True)
        
        summary = df_filtered.groupby('month_number')['retention_rate'].agg(['mean', 'std', 'min', 'max']).round(2)
        summary.columns = ['Avg Retention %', 'Std Dev', 'Min %', 'Max %']
        st.dataframe(summary, use_container_width=True)
        st.caption("High standard deviation means cohorts behave very differently – investigate what changed in those months (e.g., marketing campaign, website redesign).")

# ==================== DATA EXPLORER ====================
elif selected_page == "📊 Data Explorer":
    st.markdown('<div class="section-header">🔍 Data Explorer – Raw Data for Deep Dives</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>📖 Use Case:</strong> Download any underlying dataset for custom analysis in Excel or Python.
        All charts above are built from these tables. Use this page to verify numbers or combine fields.
    </div>
    """, unsafe_allow_html=True)
    
    dataset_names = list(friendly_data.keys())
    selected = st.selectbox("Select Dataset", dataset_names)
    if selected:
        df = friendly_data[selected]
        st.write(f"**Rows:** {len(df):,} | **Columns:** {len(df.columns)}")
        with st.expander("Column Information"):
            col_info = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes.values,
                'Non-Null Count': df.count().values,
                'Null %': (df.isnull().sum() / len(df) * 100).round(2).values
            })
            st.dataframe(col_info, use_container_width=True)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False)
        st.download_button(label="📥 Download CSV", data=csv, file_name=f"{selected}.csv", mime="text/csv")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #7f8c8d;'>"
    "Retail Analytics Dashboard | Powered by PostgreSQL & Streamlit<br>"
    f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
    "</p>",
    unsafe_allow_html=True
)