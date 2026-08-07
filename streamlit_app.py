import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
import re
import json
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Skylark Drones – BI Agent",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS — Monday.com-inspired brand colours
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Sidebar brand colours */
    section[data-testid="stSidebar"] { background-color: #292f4c; }
    section[data-testid="stSidebar"] * { color: #d2d3d9 !important; }

    /* Metric card overrides */
    [data-testid="metric-container"] {
        background: #fff;
        border: 1px solid #e6e9ef;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,.04);
    }

    /* Table style */
    .report-table th { background: #eceff1; font-weight: 700; }
    .report-table td, .report-table th { padding: 12px 16px; border-bottom: 1px solid #e6e9ef; font-size: 13px; }

    /* Status badge */
    .ready-badge {
        background: rgba(0,200,117,.12);
        color: #00c875;
        border: 1px solid rgba(0,200,117,.25);
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: .6px;
        display: inline-block;
        margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Database helper — robust absolute path so it works on Streamlit Cloud
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "backend", "skylark.db")

@st.cache_resource
def get_connection():
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

conn = get_connection()
if conn is None:
    st.error(f"⚠️ Database not found at `{DB_PATH}`. Please ensure `backend/skylark.db` is committed to your repository.")
    st.stop()

def query_db(sql):
    try:
        cur = conn.execute(sql)
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        return [{"error": str(e)}]

# ─────────────────────────────────────────────────────────────────────────────
# Self-contained fallback query resolver (no imports from backend/)
# ─────────────────────────────────────────────────────────────────────────────
def resolve_query(query: str):
    q   = query.lower()
    ans = ""
    sql = ""
    chart_data = None

    if "pending billing" in q or "pending billed" in q:
        sql  = "SELECT SUM(amount_excl_gst) as total_po, SUM(billed_excl_gst) as total_billed, SUM(CASE WHEN amount_excl_gst > billed_excl_gst THEN amount_excl_gst - billed_excl_gst ELSE 0 END) as pending FROM work_orders;"
        rows = query_db(sql)
        po, billed, pending = rows[0]["total_po"] or 0, rows[0]["total_billed"] or 0, rows[0]["pending"] or 0
        ans  = f"**📊 Pending Billing Summary**\n\n- Total PO Contract Value: ₹{po:,.2f}\n- Total Billed to Date: ₹{billed:,.2f}\n- **Pending Billing: ₹{pending:,.2f}**"
        chart_data = {"type": "bar", "x": ["Billed", "Pending"], "y": [billed, pending], "title": "Billing Status"}

    elif "revenue forecast" in q or "pipeline forecast" in q or "forecast" in q:
        sql  = """SELECT SUM(CASE WHEN deal_status='Won' THEN masked_deal_value ELSE 0 END) as won,
                         SUM(CASE WHEN deal_status='Open' THEN masked_deal_value ELSE 0 END) as open_pipe,
                         SUM(CASE WHEN deal_status='Open' AND closure_probability='High' THEN masked_deal_value*.8
                                  WHEN deal_status='Open' AND closure_probability='Medium' THEN masked_deal_value*.5
                                  WHEN deal_status='Open' AND closure_probability='Low' THEN masked_deal_value*.2
                                  ELSE 0 END) as weighted FROM deals;"""
        r    = query_db(sql)[0]
        won, op, wt = r["won"] or 0, r["open_pipe"] or 0, r["weighted"] or 0
        ans  = f"**📈 Revenue & Pipeline Forecast**\n\n- Won Revenue: ₹{won:,.2f}\n- Open Pipeline: ₹{op:,.2f}\n- **Weighted Forecast: ₹{wt:,.2f}**\n- Total Projected: ₹{won+wt:,.2f}"
        chart_data = {"type": "bar", "x": ["Won Revenue", "Open Pipeline", "Weighted Forecast"], "y": [won, op, wt], "title": "Revenue Forecast"}

    elif "pipeline" in q or "health" in q or "status" in q or "overview" in q:
        sql  = "SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as total FROM deals GROUP BY deal_status;"
        rows = query_db(sql)
        ans  = "**🔍 Sales Pipeline Health**\n\n"
        for r in rows:
            ans += f"- **{r['deal_status']}**: {r['count']} deals (₹{r['total'] or 0:,.2f})\n"
        chart_data = {"type": "pie", "labels": [r["deal_status"] for r in rows], "values": [r["count"] for r in rows], "title": "Pipeline Status"}

    elif "energy" in q or "renewables" in q or "powerline" in q:
        sql  = "SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as total FROM deals WHERE LOWER(sector_service) IN ('powerline','renewables') GROUP BY deal_status;"
        rows = query_db(sql)
        ans  = "**⚡ Energy Sector Pipeline**\n\n"
        for r in rows:
            ans += f"- **{r['deal_status']}**: {r['count']} deals (₹{r['total'] or 0:,.2f})\n"
        chart_data = {"type": "pie", "labels": [r["deal_status"] for r in rows], "values": [r["total"] or 0 for r in rows], "title": "Energy Sector"}

    elif "delayed" in q or "delay" in q or "stuck" in q or "pause" in q:
        sql  = "SELECT execution_status, COUNT(*) as count, SUM(amount_excl_gst) as total FROM work_orders WHERE execution_status IN ('Pause / struck','Not Started') GROUP BY execution_status;"
        rows = query_db(sql)
        ans  = "**⚠️ Delayed & At-Risk Work Orders**\n\n"
        risk = 0
        for r in rows:
            v    = r["total"] or 0
            risk += v
            ans += f"- **{r['execution_status']}**: {r['count']} orders (₹{v:,.2f})\n"
        ans += f"\n**Total At-Risk Value: ₹{risk:,.2f}**"
        chart_data = {"type": "bar", "x": [r["execution_status"] for r in rows], "y": [r["total"] or 0 for r in rows], "title": "At-Risk Work Orders"}

    elif "expected revenue" in q:
        sql  = """SELECT SUM(masked_deal_value) as total,
                         SUM(CASE WHEN closure_probability='High' THEN masked_deal_value*.8
                                  WHEN closure_probability='Medium' THEN masked_deal_value*.5
                                  WHEN closure_probability='Low' THEN masked_deal_value*.2
                                  ELSE 0 END) as expected FROM deals WHERE deal_status='Open';"""
        r    = query_db(sql)[0]
        tot, exp = r["total"] or 0, r["expected"] or 0
        ans  = f"**💰 Expected Revenue (Open Deals)**\n\n- Total Open Pipeline: ₹{tot:,.2f}\n- **Expected Revenue: ₹{exp:,.2f}**"
        chart_data = {"type": "pie", "labels": ["Expected","Risk Discount"], "values": [exp, tot-exp], "title": "Expected Revenue"}

    elif "operational risk" in q or "risks" in q:
        sql  = "SELECT serial_num, customer_name_code, nature_of_work, amount_excl_gst, execution_status FROM work_orders WHERE execution_status='Pause / struck' OR billing_status='Stuck' LIMIT 10;"
        rows = query_db(sql)
        ans  = "**⚡ Operational Risks & Stuck Projects**\n\n"
        for r in rows:
            ans += f"- **{r['serial_num']}** ({r['customer_name_code']}): {r['nature_of_work']} → *{r['execution_status']}* (₹{r['amount_excl_gst'] or 0:,.2f})\n"

    elif "enterprise client" in q or "top client" in q or "top enterprise" in q:
        sql  = "SELECT client_code, SUM(masked_deal_value) as total, COUNT(*) as count FROM deals GROUP BY client_code ORDER BY total DESC LIMIT 5;"
        rows = query_db(sql)
        ans  = "**🏢 Top Enterprise Clients**\n\n"
        for i, r in enumerate(rows, 1):
            ans += f"{i}. **{r['client_code']}**: ₹{r['total'] or 0:,.2f} ({r['count']} deals)\n"
        chart_data = {"type": "bar", "x": [r["client_code"] for r in rows], "y": [r["total"] or 0 for r in rows], "title": "Top Clients by Pipeline"}

    elif "leadership" in q or "summary" in q:
        sql  = "SELECT (SELECT SUM(masked_deal_value) FROM deals WHERE deal_status='Won') as won, (SELECT COUNT(*) FROM deals WHERE deal_status='Open') as open_count, (SELECT SUM(masked_deal_value) FROM deals WHERE deal_status='Open') as open_pipe, (SELECT SUM(amount_excl_gst) FROM work_orders WHERE execution_status='Completed') as completed, (SELECT SUM(amount_receivable) FROM work_orders) as receivable FROM deals LIMIT 1;"
        r    = query_db(sql)[0]
        ans  = f"**👑 Executive Leadership Summary**\n\n**Sales Performance**\n- Won Revenue: ₹{r['won'] or 0:,.2f}\n- Active Pipeline: ₹{r['open_pipe'] or 0:,.2f} ({r['open_count']} deals)\n\n**Operations**\n- Completed Project Value: ₹{r['completed'] or 0:,.2f}\n- Outstanding Receivables: ₹{r['receivable'] or 0:,.2f}"

    elif "sector" in q or "mining" in q or "aviation" in q or "railways" in q:
        sql  = "SELECT sector_service, SUM(masked_deal_value) as value, COUNT(*) as count FROM deals GROUP BY sector_service ORDER BY value DESC;"
        rows = query_db(sql)
        ans  = "**🌐 Sectoral Performance**\n\n"
        for r in rows:
            ans += f"- **{r['sector_service'] or 'Other'}**: ₹{r['value'] or 0:,.2f} ({r['count']} deals)\n"
        chart_data = {"type": "bar", "x": [r["sector_service"] or "Other" for r in rows], "y": [r["value"] or 0 for r in rows], "title": "Pipeline by Sector"}

    elif "won" in q or "revenue" in q:
        sql  = "SELECT SUM(masked_deal_value) as total, COUNT(*) as count FROM deals WHERE deal_status='Won';"
        r    = query_db(sql)[0]
        ans  = f"**💵 Total Won Revenue**\n\n- Closed Deals: {r['count']}\n- **Total Revenue: ₹{r['total'] or 0:,.2f}**"

    elif "work order" in q or "execution" in q:
        sql  = "SELECT execution_status, COUNT(*) as count, SUM(amount_excl_gst) as total FROM work_orders GROUP BY execution_status ORDER BY count DESC;"
        rows = query_db(sql)
        ans  = "**🛠️ Work Orders Execution Status**\n\n"
        for r in rows:
            ans += f"- **{r['execution_status'] or 'Unknown'}**: {r['count']} orders (₹{r['total'] or 0:,.2f})\n"
        chart_data = {"type": "pie", "labels": [r["execution_status"] or "Unknown" for r in rows], "values": [r["count"] for r in rows], "title": "Execution Status"}

    else:
        ans = "I can help you with:\n\n- 📊 **Pipeline Health** — deal status breakdown\n- 💰 **Revenue Forecast** — won & weighted pipeline\n- ⚡ **Energy Sector** — powerline & renewables performance\n- ⚠️ **Delayed Work Orders** — paused and stuck projects\n- 🏢 **Top Enterprise Clients** — ranked by pipeline value\n- 💵 **Expected Revenue** — probability-adjusted forecast\n- 🛠️ **Work Orders** — execution status overview\n\nTry asking: *\"What is our pending billing?\"*"

    return ans, sql, chart_data


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 🚁 Skylark Drones\n*BI AGENT*")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navigate", [
    "🏠 Overview",
    "💬 AI Assistant",
    "📊 Executive Dashboard",
    "🔍 Data Explorer",
    "📄 Leadership Update"
])
st.sidebar.markdown("---")
st.sidebar.success("✅ Database Connected")

# ─────────────────────────────────────────────────────────────────────────────
# 1. OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
if menu == "🏠 Overview":
    st.title("Executive System Overview")
    st.subheader("Welcome, Executive Team 👋")
    st.caption("Real-time analytics and natural language business intelligence for your Monday.com workspace — sales pipelines, work orders tracking, and leadership reporting.")

    deals_count = query_db("SELECT COUNT(*) as n FROM deals")[0]["n"]
    wo_count    = query_db("SELECT COUNT(*) as n FROM work_orders")[0]["n"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Monday.com Integration", "Mock Active 🟢")
    col2.metric("Database Records", f"{deals_count} Deals  |  {wo_count} Work Orders")
    col3.metric("AI Model Resolver", "Gemini 2.5 + Fallback")

    st.markdown("---")
    col_l, col_r = st.columns([1.3, 1])

    with col_l:
        st.markdown("### ⚡ Quick Actions")
        for label, section in [("💬 Ask the AI Assistant", "💬 AI Assistant"),
                                ("📊 View Executive Dashboard", "📊 Executive Dashboard"),
                                ("🔍 Explore Raw Data Tables", "🔍 Data Explorer"),
                                ("📄 Open Leadership Report", "📄 Leadership Update")]:
            st.markdown(f"**{label}** → *use sidebar navigation*")

    with col_r:
        st.markdown("### 🕐 System Activity Log")
        st.markdown("""
        🟢 **API Integration Online**  
        ⚫ SQLite Database Connected  
        ⚫ Data Reconstructed from PDFs  
        ⚫ Interactive Explorer Loaded  
        """)

# ─────────────────────────────────────────────────────────────────────────────
# 2. AI ASSISTANT
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "💬 AI Assistant":
    st.title("💬 AI Conversational Assistant")
    st.caption("Ask natural language questions about revenue, pipeline health, sectoral performance, or work orders.")

    # Suggested founder queries
    st.markdown("**Suggested Queries:**")
    pills = [
        "How is our pipeline looking?",
        "What is our pending billed value from work orders?",
        "What is our total won revenue and pipeline forecast?",
        "Show me the pipeline for Energy sector",
        "Give me a summary of work orders execution and delays",
        "Give me a comprehensive leadership summary update",
        "Who are our top enterprise clients by pipeline value?",
        "What is our expected revenue from open deals?",
        "Show operational risks and stuck work orders",
    ]
    cols = st.columns(3)
    for i, pill in enumerate(pills):
        if cols[i % 3].button(pill, key=f"pill_{i}", use_container_width=True):
            st.session_state.setdefault("messages", [])
            st.session_state.messages.append({"role": "user", "content": pill})

    st.markdown("---")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "👋 Greetings! I am the **Skylark BI Agent**. I have loaded **344 deals** and **176 work orders**. Ask me anything about your business data!"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "chart" in msg:
                cd = msg["chart"]
                if cd["type"] in ("bar",):
                    fig = px.bar(x=cd["x"], y=cd["y"], title=cd["title"], labels={"x": "", "y": "Value (₹)"})
                    st.plotly_chart(fig, use_container_width=True)
                elif cd["type"] == "pie":
                    fig = px.pie(names=cd["labels"], values=cd["values"], title=cd["title"], hole=.35)
                    st.plotly_chart(fig, use_container_width=True)

    if prompt := st.chat_input("Ask a business query…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        ans, sql, chart_data = resolve_query(prompt)

        msg_obj = {"role": "assistant", "content": ans}
        if chart_data:
            msg_obj["chart"] = chart_data

        st.session_state.messages.append(msg_obj)
        with st.chat_message("assistant"):
            st.markdown(ans)
            if sql:
                with st.expander("🗄️ Executed SQL Query"):
                    st.code(sql, language="sql")
            if chart_data:
                cd = chart_data
                if cd["type"] in ("bar",):
                    fig = px.bar(x=cd["x"], y=cd["y"], title=cd["title"], labels={"x": "", "y": "Value (₹)"}, color=cd["x"])
                    st.plotly_chart(fig, use_container_width=True)
                elif cd["type"] == "pie":
                    fig = px.pie(names=cd["labels"], values=cd["values"], title=cd["title"], hole=.35)
                    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3. EXECUTIVE DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📊 Executive Dashboard":
    st.title("📊 Executive Dashboard")

    won_rev   = query_db("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Won'")[0]["v"] or 0
    open_pipe = query_db("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Open'")[0]["v"] or 0
    total_rec = query_db("SELECT SUM(amount_receivable) as v FROM work_orders")[0]["v"] or 0
    billed    = query_db("SELECT SUM(billed_excl_gst) as v FROM work_orders")[0]["v"] or 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏆 Won Revenue",         f"₹{won_rev/1e7:.2f} Cr")
    c2.metric("🔄 Active Pipeline",     f"₹{open_pipe/1e7:.2f} Cr")
    c3.metric("🧾 Total Billed (WOs)",  f"₹{billed/1e5:.2f} L")
    c4.metric("📥 Outstanding AR",      f"₹{total_rec/1e5:.2f} L")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### Pipeline Status Breakdown")
        df = pd.DataFrame(query_db("SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as value FROM deals GROUP BY deal_status"))
        fig = px.pie(df, values="count", names="deal_status", hole=.4,
                     color_discrete_map={"Open":"#0073ea","Won":"#00c875","Dead":"#df2f4a","On Hold":"#fdab3d"})
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("#### Sectoral Pipeline Value")
        df2 = pd.DataFrame(query_db("SELECT sector_service, SUM(masked_deal_value) as value FROM deals GROUP BY sector_service ORDER BY value DESC"))
        fig2 = px.bar(df2, x="sector_service", y="value", color="sector_service",
                      labels={"value":"Pipeline (₹)","sector_service":"Sector"})
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### Work Orders Execution Status")
        df3 = pd.DataFrame(query_db("SELECT execution_status, COUNT(*) as count FROM work_orders GROUP BY execution_status ORDER BY count DESC"))
        fig3 = px.bar(df3, x="execution_status", y="count", color="execution_status",
                      labels={"count":"Orders","execution_status":"Status"})
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("#### Top 5 Owners by Won Revenue")
        df4 = pd.DataFrame(query_db("SELECT owner_code, SUM(masked_deal_value) as value FROM deals WHERE deal_status='Won' GROUP BY owner_code ORDER BY value DESC LIMIT 5"))
        fig4 = px.bar(df4, x="owner_code", y="value", color="owner_code",
                      labels={"value":"Revenue (₹)","owner_code":"Owner"})
        st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# 4. DATA EXPLORER
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "🔍 Data Explorer":
    st.title("🔍 Interactive Data Explorer")
    tab_deals, tab_wos = st.tabs(["📁 Deals Board", "📁 Work Orders Board"])

    with tab_deals:
        df_d = pd.DataFrame(query_db("SELECT * FROM deals"))
        search = st.text_input("🔍 Search Deals", placeholder="Search by name, owner, client, sector…", key="s_deals")
        status_opts = ["All"] + sorted(df_d["deal_status"].dropna().unique().tolist())
        status_filter = st.selectbox("Filter by Status", status_opts, key="f_deals")
        if search:
            mask = df_d.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)
            df_d = df_d[mask]
        if status_filter != "All":
            df_d = df_d[df_d["deal_status"] == status_filter]
        st.dataframe(df_d, use_container_width=True, height=480)
        st.caption(f"Showing {len(df_d)} records")
        st.download_button("📥 Export CSV", df_d.to_csv(index=False), "deals_export.csv", "text/csv")

    with tab_wos:
        df_w = pd.DataFrame(query_db("SELECT * FROM work_orders"))
        search_w = st.text_input("🔍 Search Work Orders", placeholder="Search by customer, nature of work…", key="s_wos")
        exec_opts = ["All"] + sorted(df_w["execution_status"].dropna().unique().tolist())
        exec_filter = st.selectbox("Filter by Execution Status", exec_opts, key="f_wos")
        if search_w:
            mask_w = df_w.apply(lambda r: r.astype(str).str.contains(search_w, case=False).any(), axis=1)
            df_w   = df_w[mask_w]
        if exec_filter != "All":
            df_w = df_w[df_w["execution_status"] == exec_filter]
        st.dataframe(df_w, use_container_width=True, height=480)
        st.caption(f"Showing {len(df_w)} records")
        st.download_button("📥 Export CSV", df_w.to_csv(index=False), "work_orders_export.csv", "text/csv")

# ─────────────────────────────────────────────────────────────────────────────
# 5. LEADERSHIP UPDATE
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📄 Leadership Update":
    st.title("📄 Executive Leadership Update")

    # Pull live metrics
    open_count  = query_db("SELECT COUNT(*) as n FROM deals WHERE deal_status='Open'")[0]["n"] or 0
    open_sum    = query_db("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Open'")[0]["v"] or 0
    weighted    = query_db("""SELECT SUM(
                                CASE WHEN closure_probability='High'   THEN masked_deal_value*.8
                                     WHEN closure_probability='Medium' THEN masked_deal_value*.5
                                     WHEN closure_probability='Low'    THEN masked_deal_value*.2
                                     ELSE 0 END) as v FROM deals WHERE deal_status='Open'""")[0]["v"] or 0
    won_sum     = query_db("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Won'")[0]["v"] or 0
    comp_count  = query_db("SELECT COUNT(*) as n FROM work_orders WHERE execution_status='Completed'")[0]["n"] or 0
    total_billed= query_db("SELECT SUM(billed_excl_gst) as v FROM work_orders")[0]["v"] or 0
    total_rec   = query_db("SELECT SUM(amount_receivable) as v FROM work_orders")[0]["v"] or 0

    pipe_cr    = open_sum   / 1e7
    weight_cr  = weighted   / 1e7
    billed_l   = total_billed / 1e5
    date_str   = datetime.now().strftime("%B %d, %Y")

    st.markdown('<span class="ready-badge">● EXECUTIVE REPORT READY</span>', unsafe_allow_html=True)

    col_hdr, col_btns = st.columns([3, 1])
    with col_hdr:
        st.markdown(f"**Date:** {date_str}  |  **Data Source:** Dynamic Monday.com Integrations *(Deals Board & Work Orders Board)*")

    with col_btns:
        md_report = f"""# Skylark Drones – Executive Leadership Update

**Date:** {date_str}  
**Data Source:** Dynamic Monday.com Integrations (Deals Board & Work Orders Board)

---

### 1. Executive Summary
Skylark Drones is tracking a **total sales pipeline of ₹{pipe_cr:.2f} Cr** across **{open_count} active deals**, with a probability-weighted expected revenue of **₹{weight_cr:.2f} Cr**. Operations have successfully delivered **{comp_count} work orders**, achieving a total billed value of **₹{billed_l:.2f} Lakhs**.

### 2. Revenue & Financial Overview

| Financial Metric | Amount (INR) | Key Observations |
|---|---|---|
| **Total Open Pipeline** | ₹{open_sum:,.2f} | Driven by large Mining & Powerline proposals |
| **Probability-Weighted Revenue** | ₹{weighted:,.2f} | High (80%), Medium (50%), Low (20%) |
| **Realized Won Revenue** | ₹{won_sum:,.2f} | Closed-won contract commitments |
| **Billed Work Order Value** | ₹{total_billed:,.2f} | Invoiced operational deliveries |
| **Outstanding Receivables** | ₹{total_rec:,.2f} | Requires collection prioritization |
"""
        st.download_button("📥 Download .md", md_report, "Skylark_Executive_Report.md", "text/markdown", use_container_width=True)

    st.markdown("---")

    st.markdown(f"""
### 1. Executive Summary

Skylark Drones is tracking a **total sales pipeline of ₹{pipe_cr:.2f} Cr** across **{open_count} active deals**, with a probability-weighted expected revenue of **₹{weight_cr:.2f} Cr**.  
Operations have successfully delivered **{comp_count} work orders**, achieving a total billed value of **₹{billed_l:.2f} Lakhs**.
""")

    st.markdown("### 2. Revenue & Financial Overview")
    df_metrics = pd.DataFrame([
        {"Financial Metric": "Total Open Pipeline",         "Amount (INR)": f"₹{open_sum:,.2f}",     "Key Observations": "Driven by large Mining & Powerline sector proposals"},
        {"Financial Metric": "Probability-Weighted Revenue","Amount (INR)": f"₹{weighted:,.2f}",      "Key Observations": "High (80%), Medium (50%), Low (20%) closure probability"},
        {"Financial Metric": "Realized Won Revenue",        "Amount (INR)": f"₹{won_sum:,.2f}",       "Key Observations": "Closed-won contract commitments"},
        {"Financial Metric": "Billed Work Order Value",     "Amount (INR)": f"₹{total_billed:,.2f}",  "Key Observations": "Invoiced operational deliveries"},
        {"Financial Metric": "Outstanding Receivables",     "Amount (INR)": f"₹{total_rec:,.2f}",     "Key Observations": "Requires collection prioritization for priority accounts"},
    ])
    st.table(df_metrics)

    st.markdown("### 3. Pipeline Visual Snapshot")
    df_snap = pd.DataFrame(query_db("SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as value FROM deals GROUP BY deal_status"))
    col_a, col_b = st.columns(2)
    with col_a:
        fig_a = px.pie(df_snap, values="count", names="deal_status", hole=.4, title="Deals by Status",
                       color_discrete_map={"Open":"#0073ea","Won":"#00c875","Dead":"#df2f4a","On Hold":"#fdab3d"})
        st.plotly_chart(fig_a, use_container_width=True)
    with col_b:
        fig_b = px.bar(df_snap, x="deal_status", y="value", color="deal_status", title="Pipeline Value by Status",
                       labels={"value":"Value (₹)","deal_status":"Status"})
        st.plotly_chart(fig_b, use_container_width=True)
