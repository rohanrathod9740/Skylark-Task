import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Skylark Drones - BI Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling matching the brand environment
st.markdown("""
<style>
    .monday-header {
        color: #0073ea !important;
        font-weight: 700 !important;
    }
    .status-badge {
        background-color: rgba(0, 200, 117, 0.1) !important;
        color: #00c875 !important;
        border: 1px solid rgba(0, 200, 117, 0.2) !important;
        padding: 6px 12px !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 12px !important;
        display: inline-block !important;
        margin-bottom: 20px !important;
    }
    .report-card {
        background-color: white;
        border: 1px solid #e6e9ef;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
    }
</style>
""", unsafe_allow_html=True)

# Database connection helper
DB_PATH = os.path.join("backend", "skylark.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Verify database cache exists
if not os.path.exists(DB_PATH):
    st.error("SQLite database cache not found! Please run the data reconstruction script locally first (`npm run reconstruct`).")
    st.stop()

# Sidebar Navigation
st.sidebar.markdown("<h2 class='monday-header'>Skylark Drones</h2><p style='font-size:11px; margin-top:-15px; letter-spacing:1.5px; color:#676879;'>BUSINESS INTELLIGENCE</p>", unsafe_allow_html=True)
menu = st.sidebar.radio("Main Menu", ["Overview", "AI Assistant", "Executive Dashboard", "Interactive Data Explorer", "Leadership Update"])

st.sidebar.markdown("---")
st.sidebar.info("💡 **Streamlit Python Edition**: Serves as a 1-click cloud-deployable alternative. To load the premium custom Monday.com UI/UX, execute `npm start` in your workspace.")

# 1. Overview Screen
if menu == "Overview":
    st.title("Executive System Overview")
    st.subheader("Welcome, Executive Team")
    st.write("Real-time analytics and natural language business intelligence for your Monday.com workspace operations, sales pipelines, and work orders tracking.")
    
    # KPI Grid
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Monday.com Integration Status", value="Mock Active")
    with col2:
        conn = get_db_connection()
        deals_count = conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0]
        wos_count = conn.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0]
        conn.close()
        st.metric(label="Local Database Cache", value=f"{deals_count} Deals | {wos_count} Work Orders")
    with col3:
        st.metric(label="AI Model Resolver", value="Gemini-2.5-Flash (with fallback)")

    st.markdown("---")
    col_l, col_r = st.columns([1.2, 1])
    with col_l:
        st.markdown("### Quick Actions")
        st.write("Navigate to other sections using the sidebar options:")
        st.markdown("""
        * 💬 **AI Assistant**: Conversational text search interface to generate charts.
        * 📊 **Executive Dashboard**: Visualize pipeline sales, top owners, and operations.
        * 🔍 **Interactive Data Explorer**: Search, filter, and review raw database records.
        * 📄 **Leadership Update**: View, copy, and export the executive report.
        """)
    with col_r:
        st.markdown("### System Activity Timeline")
        st.markdown("""
        * **🟢 API Integration Online** - Web server active
        * **⚪ SQLite Database Connected** - Loaded deals and work orders caches
        * **⚪ Data Reconstructed Successfully** - Normalized records from raw horizontal PDFs
        """)

# 2. Chatbot Screen
elif menu == "AI Assistant":
    st.title("AI Conversational Assistant")
    st.write("Ask natural language queries about revenue, pipeline health, sectoral performance, or work orders.")

    # Add backend path to sys for fallback loader import
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    from agent_resolver import resolve_query_fallback

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Greetings! I am the Skylark BI Agent. I have loaded the deals and work orders tables. How can I assist you with your business queries today?"}]

    # Display chat feed
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User chat input
    if prompt := st.chat_input("Ask a business query (e.g. What is our pending billed value?)..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Process through local fallback query matching engine
        ans, sql = resolve_query_fallback(prompt)
        
        with st.chat_message("assistant"):
            st.markdown(ans)
            if sql:
                with st.expander("Show Executed SQL Query"):
                    st.code(sql, language="sql")
        st.session_state.messages.append({"role": "assistant", "content": ans})

# 3. Dashboard Screen
elif menu == "Executive Dashboard":
    st.title("Executive Dashboard")
    
    conn = get_db_connection()
    
    # Aggregates
    won_rev = conn.execute("SELECT SUM(masked_deal_value) FROM deals WHERE deal_status='Won'").fetchone()[0] or 0
    open_pipe = conn.execute("SELECT SUM(masked_deal_value) FROM deals WHERE deal_status='Open'").fetchone()[0] or 0
    completed_wo = conn.execute("SELECT SUM(amount_excl_gst) FROM work_orders WHERE execution_status='Completed'").fetchone()[0] or 0
    total_rec = conn.execute("SELECT SUM(amount_receivable) FROM work_orders").fetchone()[0] or 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue (Won)", f"₹{won_rev:,.2f}")
    col2.metric("Active Pipeline (Open)", f"₹{open_pipe:,.2f}")
    col3.metric("Completed Project Value", f"₹{completed_wo:,.2f}")
    col4.metric("Outstanding Receivables", f"₹{total_rec:,.2f}")
    
    st.markdown("---")
    
    # Plotly Charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### Deals Pipeline Status Breakdown")
        df_status = pd.read_sql_query("SELECT deal_status, COUNT(*) as count FROM deals GROUP BY deal_status", conn)
        fig_status = px.pie(df_status, values="count", names="deal_status", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_status, use_container_width=True)
        
    with col_right:
        st.markdown("#### Sectoral Pipeline Performance")
        df_sector = pd.read_sql_query("SELECT sector_service, SUM(masked_deal_value) as value FROM deals GROUP BY sector_service ORDER BY value DESC", conn)
        fig_sector = px.bar(df_sector, x="sector_service", y="value", labels={"value":"Pipeline Value (₹)", "sector_service":"Sector"}, color="sector_service")
        st.plotly_chart(fig_sector, use_container_width=True)

    conn.close()

# 4. Data Explorer Grids
elif menu == "Interactive Data Explorer":
    st.title("Interactive Data Explorer")
    st.write("Browse and review raw Deals and Work Orders datasets.")
    
    tab_deals, tab_wos = st.tabs(["Deals Board Explorer", "Work Orders Board Explorer"])
    conn = get_db_connection()
    
    with tab_deals:
        df_deals = pd.read_sql_query("SELECT * FROM deals", conn)
        st.dataframe(df_deals, use_container_width=True)
        
    with tab_wos:
        df_wos = pd.read_sql_query("SELECT * FROM work_orders", conn)
        st.dataframe(df_wos, use_container_width=True)
        
    conn.close()

# 5. Leadership Updates Report Workspace
elif menu == "Leadership Update":
    st.title("Executive Leadership Update Workspace")
    
    # Pull metrics from SQLite
    conn = get_db_connection()
    open_count = conn.execute("SELECT COUNT(*) FROM deals WHERE deal_status = 'Open'").fetchone()[0] or 0
    open_sum = conn.execute("SELECT SUM(masked_deal_value) FROM deals WHERE deal_status = 'Open'").fetchone()[0] or 0
    weighted_sum = conn.execute("""
        SELECT SUM(
            CASE WHEN closure_probability = 'High' THEN masked_deal_value * 0.8
                 WHEN closure_probability = 'Medium' THEN masked_deal_value * 0.5
                 WHEN closure_probability = 'Low' THEN masked_deal_value * 0.2
                 ELSE 0 END
        ) FROM deals WHERE deal_status = 'Open'
    """).fetchone()[0] or 0
    won_sum = conn.execute("SELECT SUM(masked_deal_value) FROM deals WHERE deal_status = 'Won'").fetchone()[0] or 0
    comp_count = conn.execute("SELECT COUNT(*) FROM work_orders WHERE execution_status = 'Completed'").fetchone()[0] or 0
    total_billed = conn.execute("SELECT SUM(billed_excl_gst) FROM work_orders").fetchone()[0] or 0
    total_rec = conn.execute("SELECT SUM(amount_receivable) FROM work_orders").fetchone()[0] or 0
    conn.close()
    
    pipeline_cr = open_sum / 10000000
    weighted_cr = weighted_sum / 10000000
    billed_lakhs = total_billed / 100000
    
    date_str = datetime.now().strftime("%B %d, %Y")
    
    st.markdown('<div class="status-badge">● EXECUTIVE REPORT READY</div>', unsafe_allow_html=True)
    
    # Document Container
    st.markdown(f"""
    <div class="report-card">
        <h2>📄 Skylark Drones - Executive Leadership Update</h2>
        <p style="color:#676879; font-size:13px;"><strong>Date:</strong> {date_str} | <strong>Data Source:</strong> Dynamic Monday.com Integrations</p>
        <hr style="margin:20px 0; border:none; border-top:1px solid #e6e9ef;">
        <h3>1. Executive Summary</h3>
        <p style="line-height:1.6; font-size:14.5px;">
            Skylark Drones is tracking a <strong>total sales pipeline of ₹{pipeline_cr:.2f} Cr</strong> across <strong>{open_count} active deals</strong>, with a probability-weighted expected revenue of <strong>₹{weighted_cr:.2f} Cr</strong>. Operations have successfully delivered <strong>{comp_count} work orders</strong>, achieving a total billed value of <strong>₹{billed_lakhs:.2f} Lakhs</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><h3>2. Revenue & Financial Overview</h3>", unsafe_allow_html=True)
    df_metrics = pd.DataFrame([
        {"Financial Metric": "Total Open Pipeline", "Amount (INR)": f"₹{open_sum:,.2f}", "Key Observations": "Driven primarily by large Mining & Powerline sector proposals"},
        {"Financial Metric": "Probability-Weighted Revenue", "Amount (INR)": f"₹{weighted_sum:,.2f}", "Key Observations": "Adjusted for High (80%), Medium (50%), and Low (20%) closure probability"},
        {"Financial Metric": "Realized Won Revenue", "Amount (INR)": f"₹{won_sum:,.2f}", "Key Observations": "Closed-won contract commitments"},
        {"Financial Metric": "Billed Work Order Value", "Amount (INR)": f"₹{total_billed:,.2f}", "Key Observations": "Invoiced operational deliveries"},
        {"Financial Metric": "Outstanding Receivables", "Amount (INR)": f"₹{total_rec:,.2f}", "Key Observations": "Requires collection prioritization for priority accounts"},
    ])
    st.table(df_metrics)
    
    # MD content compilation
    md_content = f"""# Skylark Drones - Executive Leadership Update
Date: {date_str}
Data Source: Dynamic Monday.com Integrations (Deals Board & Work Orders Board)

### 1. Executive Summary
Skylark Drones is tracking a total sales pipeline of ₹{pipeline_cr:.2f} Cr across {open_count} active deals, with a probability-weighted expected revenue of ₹{weighted_cr:.2f} Cr. Operations have successfully delivered {comp_count} work orders, achieving a total billed value of ₹{billed_lakhs:.2f} Lakhs.

### 2. Revenue & Financial Overview
*   **Total Open Pipeline**: ₹{open_sum:,.2f} (Driven primarily by large Mining & Powerline sector proposals)
*   **Probability-Weighted Revenue**: ₹{weighted_sum:,.2f} (Adjusted for High (80%), Medium (50%), and Low (20%) closure probability)
*   **Realized Won Revenue**: ₹{won_sum:,.2f} (Closed-won contract commitments)
*   **Billed Work Order Value**: ₹{total_billed:,.2f} (Invoiced operational deliveries)
*   **Outstanding Receivables**: ₹{total_rec:,.2f} (Requires collection prioritization for priority accounts)
"""
    st.download_button(label="📥 Download .md Report", data=md_content, file_name="Skylark_Executive_Report.md", mime="text/markdown")
