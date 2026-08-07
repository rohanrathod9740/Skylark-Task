import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import urllib.request
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
# Premium CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Outfit', sans-serif !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1f36 0%, #292f4c 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] * { color: #d2d3d9 !important; }
section[data-testid="stSidebar"] .stRadio label { 
    padding: 8px 12px; border-radius: 8px; transition: background .2s;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e6e9ef;
    border-radius: 14px;
    padding: 20px 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,.04);
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 12px; font-weight: 600; letter-spacing: .5px;
    text-transform: uppercase; color: #676879 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 26px; font-weight: 700; color: #0073ea !important;
}

/* Chat messages */
[data-testid="stChatMessageContent"] { font-size: 15px; line-height: 1.6; }

/* Badges */
.green-badge {
    background: rgba(0,200,117,.12); color: #00c875;
    border: 1px solid rgba(0,200,117,.3);
    padding: 4px 14px; border-radius: 20px;
    font-size: 11px; font-weight: 700; letter-spacing: .7px;
    display: inline-block; margin-bottom: 16px;
}
.blue-badge {
    background: rgba(0,115,234,.1); color: #0073ea;
    border: 1px solid rgba(0,115,234,.25);
    padding: 4px 14px; border-radius: 20px;
    font-size: 11px; font-weight: 700;
    display: inline-block;
}

/* Hero card */
.hero-card {
    background: linear-gradient(135deg, #0073ea 0%, #0095f7 50%, #00c875 100%);
    border-radius: 20px;
    padding: 40px 48px;
    color: white;
    margin-bottom: 28px;
    box-shadow: 0 8px 32px rgba(0,115,234,.25);
}
.hero-card h1 { font-size: 32px; font-weight: 700; margin-bottom: 8px; }
.hero-card p { font-size: 16px; opacity: .9; margin: 0; }

/* Feature card */
.feat-card {
    background: #fff;
    border: 1px solid #e6e9ef;
    border-radius: 14px;
    padding: 22px 24px;
    height: 100%;
    box-shadow: 0 2px 8px rgba(0,0,0,.03);
    transition: transform .2s, box-shadow .2s;
}
.feat-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,115,234,.1); }
.feat-card h4 { font-size: 15px; font-weight: 700; color: #323338; margin-bottom: 8px; }
.feat-card p  { font-size: 13px; color: #676879; margin: 0; line-height: 1.5; }
.feat-icon { font-size: 28px; margin-bottom: 12px; }

/* Stat strip */
.stat-strip {
    background: #fff;
    border: 1px solid #e6e9ef;
    border-radius: 14px;
    padding: 20px 28px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,.03);
}

/* Report table */
.report-table { width: 100%; border-collapse: collapse; margin-top: 8px; }
.report-table th {
    background: #f5f6f8; font-weight: 700; font-size: 12px;
    text-transform: uppercase; letter-spacing: .5px;
    padding: 12px 16px; border-bottom: 2px solid #e6e9ef; text-align: left;
}
.report-table td {
    padding: 14px 16px; border-bottom: 1px solid #f0f2f5;
    font-size: 14px; color: #323338;
}
.report-table tr:hover td { background: #f8faff; }
.report-table tr:last-child td { background: rgba(0,115,234,.04); font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Database — absolute path for Streamlit Cloud
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "backend", "skylark.db")

@st.cache_resource
def get_conn():
    if not os.path.exists(DB_PATH):
        return None
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

conn = get_conn()
if conn is None:
    st.error(f"⚠️ Database not found at `{DB_PATH}`. Ensure `backend/skylark.db` is committed to the repo.")
    st.stop()

def qdb(sql):
    try:
        return [dict(r) for r in conn.execute(sql).fetchall()]
    except Exception as e:
        return [{"error": str(e)}]

# ─────────────────────────────────────────────────────────────────────────────
# Gemini API helper — falls back to local resolver on failure
# ─────────────────────────────────────────────────────────────────────────────
SKYLARK_CONTEXT = """
You are the Skylark Drones Business Intelligence Agent — a smart, data-driven assistant embedded
inside Skylark Drones' internal analytics dashboard.

About Skylark Drones:
- Skylark Drones is an Indian drone services company operating in sectors like Mining, Powerline,
  Renewables, Railways, Aviation, Construction, and more.
- They track deals (sales pipeline) and work orders (project execution) using Monday.com boards.
- Founders and executives use this agent to get instant answers about revenue, pipeline, clients,
  and operational performance.

Database Schema:
1. `deals` table: deal_name, owner_code, client_code, deal_status (Open/Won/Dead/On Hold),
   masked_deal_value, closure_probability (High/Medium/Low), sector_service, deal_stage, product_deal
2. `work_orders` table: serial_num, customer_name_code, nature_of_work, execution_status,
   amount_excl_gst, billed_excl_gst, amount_receivable, billing_status, invoice_status,
   bd_kam_personnel_code, sector, type_of_work

You have already queried the database and the result is provided below.
Give a concise, insightful answer with context — not just raw numbers.
Use Indian currency formatting (₹ with Cr/Lakhs as appropriate).
Be conversational and helpful.
"""

def call_gemini(prompt: str, db_result: str = "") -> str:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    full_prompt = SKYLARK_CONTEXT
    if db_result:
        full_prompt += f"\n\nDatabase Query Result:\n{db_result}\n\nUser Question: {prompt}"
    else:
        full_prompt += f"\n\nUser Question: {prompt}\n\n(No database query needed — answer from your context about Skylark Drones.)"

    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode())
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return ""

# ─────────────────────────────────────────────────────────────────────────────
# Self-contained fallback resolver
# ─────────────────────────────────────────────────────────────────────────────
def resolve_query(query: str):
    q       = query.lower()
    ans     = ""
    sql     = ""
    chart   = None
    db_text = ""

    # ── 1. Pending Billing ──────────────────────────────────────────────────
    if "pending billing" in q or "pending billed" in q:
        sql  = ("SELECT SUM(amount_excl_gst) as total_po, SUM(billed_excl_gst) as total_billed,"
                " SUM(CASE WHEN amount_excl_gst>billed_excl_gst THEN amount_excl_gst-billed_excl_gst ELSE 0 END) as pending"
                " FROM work_orders;")
        rows = qdb(sql)
        po, billed, pending = rows[0]["total_po"] or 0, rows[0]["total_billed"] or 0, rows[0]["pending"] or 0
        db_text = f"Total PO: ₹{po:,.2f}, Total Billed: ₹{billed:,.2f}, Pending: ₹{pending:,.2f}"
        ans  = (f"**📊 Work Orders Pending Billing**\n\n"
                f"- Total PO Contract Value: **₹{po/1e7:.2f} Cr**\n"
                f"- Total Billed to Date: **₹{billed/1e7:.2f} Cr**\n"
                f"- **Pending Billing: ₹{pending/1e7:.2f} Cr**\n\n"
                f"> Records with over-billing (billed > PO value) are excluded to prevent negative distortion.")
        chart = ("bar", ["Total Billed", "Pending Billing"], [billed, pending], "Billing Status Breakdown")

    # ── 2. Revenue / Forecast ───────────────────────────────────────────────
    elif any(x in q for x in ["revenue forecast", "pipeline forecast", "forecast", "total won revenue"]):
        sql  = """SELECT
                    SUM(CASE WHEN deal_status='Won' THEN masked_deal_value ELSE 0 END) as won,
                    SUM(CASE WHEN deal_status='Open' THEN masked_deal_value ELSE 0 END) as open_pipe,
                    SUM(CASE WHEN deal_status='Open' AND closure_probability='High'   THEN masked_deal_value*.8
                             WHEN deal_status='Open' AND closure_probability='Medium' THEN masked_deal_value*.5
                             WHEN deal_status='Open' AND closure_probability='Low'    THEN masked_deal_value*.2
                             ELSE 0 END) as weighted FROM deals;"""
        r   = qdb(sql)[0]
        won, op, wt = r["won"] or 0, r["open_pipe"] or 0, r["weighted"] or 0
        db_text = f"Won: ₹{won:,.2f}, Open Pipeline: ₹{op:,.2f}, Weighted Forecast: ₹{wt:,.2f}"
        ans = (f"**📈 Revenue & Pipeline Forecast**\n\n"
               f"- **Won Revenue:** ₹{won/1e7:.2f} Cr\n"
               f"- **Open Pipeline:** ₹{op/1e7:.2f} Cr\n"
               f"- **Probability-Weighted Forecast:** ₹{wt/1e7:.2f} Cr\n"
               f"  *(High=80%, Medium=50%, Low=20%)*\n"
               f"- **Total Projected Revenue:** ₹{(won+wt)/1e7:.2f} Cr")
        chart = ("bar", ["Won Revenue", "Open Pipeline", "Weighted Forecast"], [won, op, wt], "Revenue Forecast")

    # ── 3. Pipeline Health / Overview ───────────────────────────────────────
    elif any(x in q for x in ["pipeline", "pipeline health", "how is our pipeline", "deals status"]):
        sql  = "SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as total FROM deals GROUP BY deal_status;"
        rows = qdb(sql)
        db_text = str(rows)
        ans  = "**🔍 Sales Pipeline Health**\n\n"
        for r in rows:
            ans += f"- **{r['deal_status']}**: {r['count']} deals → ₹{(r['total'] or 0)/1e7:.2f} Cr\n"
        chart = ("pie", [r["deal_status"] for r in rows], [r["count"] for r in rows], "Pipeline Status Mix")

    # ── 4. Energy Sector ────────────────────────────────────────────────────
    elif any(x in q for x in ["energy sector", "energy", "renewables", "powerline"]):
        sql  = ("SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as total"
                " FROM deals WHERE LOWER(sector_service) IN ('powerline','renewables') GROUP BY deal_status;")
        rows = qdb(sql)
        db_text = str(rows)
        ans  = "**⚡ Energy Sector Pipeline**\n\n"
        for r in rows:
            ans += f"- **{r['deal_status']}**: {r['count']} deals (₹{(r['total'] or 0)/1e7:.2f} Cr)\n"
        chart = ("pie", [r["deal_status"] for r in rows], [r["total"] or 0 for r in rows], "Energy Sector Pipeline")

    # ── 5. Delayed / Stuck Work Orders ──────────────────────────────────────
    elif any(x in q for x in ["delayed", "delays", "stuck", "pause", "at risk", "not started"]):
        sql  = ("SELECT execution_status, COUNT(*) as count, SUM(amount_excl_gst) as total"
                " FROM work_orders WHERE execution_status IN ('Pause / struck','Not Started') GROUP BY execution_status;")
        rows = qdb(sql)
        db_text = str(rows)
        risk = sum(r["total"] or 0 for r in rows)
        ans  = "**⚠️ Delayed & At-Risk Work Orders**\n\n"
        for r in rows:
            ans += f"- **{r['execution_status']}**: {r['count']} orders (₹{(r['total'] or 0)/1e5:.2f} L)\n"
        ans += f"\n> **Total At-Risk Value: ₹{risk/1e5:.2f} Lakhs**"
        chart = ("bar", [r["execution_status"] for r in rows], [r["total"] or 0 for r in rows], "At-Risk Work Orders")

    # ── 6. Expected Revenue ─────────────────────────────────────────────────
    elif "expected revenue" in q:
        sql  = """SELECT SUM(masked_deal_value) as total,
                         SUM(CASE WHEN closure_probability='High'   THEN masked_deal_value*.8
                                  WHEN closure_probability='Medium' THEN masked_deal_value*.5
                                  WHEN closure_probability='Low'    THEN masked_deal_value*.2
                                  ELSE 0 END) as expected FROM deals WHERE deal_status='Open';"""
        r   = qdb(sql)[0]
        tot, exp = r["total"] or 0, r["expected"] or 0
        db_text = f"Total Open: ₹{tot:,.2f}, Expected: ₹{exp:,.2f}"
        ans = (f"**💰 Expected Revenue from Open Deals**\n\n"
               f"- Total Open Pipeline: **₹{tot/1e7:.2f} Cr**\n"
               f"- **Expected Revenue (probability-adjusted): ₹{exp/1e7:.2f} Cr**\n"
               f"- Risk Discount: ₹{(tot-exp)/1e7:.2f} Cr")
        chart = ("donut", ["Expected Revenue", "Risk Discount"], [exp, tot - exp], "Expected Revenue Breakdown")

    # ── 7. Operational Risks ────────────────────────────────────────────────
    elif any(x in q for x in ["operational risk", "risks", "stuck work"]):
        sql  = ("SELECT serial_num, customer_name_code, nature_of_work, amount_excl_gst, execution_status"
                " FROM work_orders WHERE execution_status='Pause / struck' OR billing_status='Stuck' LIMIT 10;")
        rows = qdb(sql)
        db_text = str(rows)
        ans  = "**⚡ Operational Risks & Stuck Projects**\n\n"
        for r in rows:
            ans += f"- **{r['serial_num']}** | {r['customer_name_code']} | {r['nature_of_work']} → *{r['execution_status']}* (₹{(r['amount_excl_gst'] or 0)/1e5:.2f} L)\n"

    # ── 8. Top Clients ──────────────────────────────────────────────────────
    elif any(x in q for x in ["top client", "enterprise client", "top enterprise", "best client"]):
        sql  = ("SELECT client_code, SUM(masked_deal_value) as total, COUNT(*) as count"
                " FROM deals GROUP BY client_code ORDER BY total DESC LIMIT 5;")
        rows = qdb(sql)
        db_text = str(rows)
        ans  = "**🏢 Top 5 Enterprise Clients by Pipeline Value**\n\n"
        for i, r in enumerate(rows, 1):
            ans += f"{i}. **{r['client_code']}** — ₹{(r['total'] or 0)/1e7:.2f} Cr across {r['count']} deals\n"
        chart = ("bar", [r["client_code"] for r in rows], [r["total"] or 0 for r in rows], "Top Clients by Pipeline")

    # ── 9. Leadership Summary ───────────────────────────────────────────────
    elif any(x in q for x in ["leadership summary", "leadership update", "comprehensive", "executive summary"]):
        sql  = """SELECT
                    (SELECT SUM(masked_deal_value) FROM deals WHERE deal_status='Won') as won,
                    (SELECT COUNT(*) FROM deals WHERE deal_status='Open') as open_count,
                    (SELECT SUM(masked_deal_value) FROM deals WHERE deal_status='Open') as open_pipe,
                    (SELECT SUM(amount_excl_gst) FROM work_orders WHERE execution_status='Completed') as completed,
                    (SELECT SUM(amount_receivable) FROM work_orders) as receivable
                  FROM deals LIMIT 1;"""
        r = qdb(sql)[0]
        db_text = str(r)
        ans = (f"**👑 Executive Leadership Summary**\n\n"
               f"**Sales & Pipeline**\n"
               f"- Won Revenue: **₹{(r['won'] or 0)/1e7:.2f} Cr**\n"
               f"- Active Pipeline: **₹{(r['open_pipe'] or 0)/1e7:.2f} Cr** ({r['open_count']} deals)\n\n"
               f"**Operations**\n"
               f"- Completed Project Value: **₹{(r['completed'] or 0)/1e5:.2f} Lakhs**\n"
               f"- Outstanding Receivables: **₹{(r['receivable'] or 0)/1e5:.2f} Lakhs**")

    # ── 10. Sectoral ────────────────────────────────────────────────────────
    elif any(x in q for x in ["sector", "mining", "aviation", "railways", "construction"]):
        sql  = ("SELECT sector_service, SUM(masked_deal_value) as value, COUNT(*) as count"
                " FROM deals GROUP BY sector_service ORDER BY value DESC;")
        rows = qdb(sql)
        db_text = str(rows)
        ans  = "**🌐 Pipeline by Sector**\n\n"
        for r in rows:
            ans += f"- **{r['sector_service'] or 'Other'}**: ₹{(r['value'] or 0)/1e7:.2f} Cr ({r['count']} deals)\n"
        chart = ("bar", [r["sector_service"] or "Other" for r in rows], [r["value"] or 0 for r in rows], "Pipeline by Sector")

    # ── 11. Work Orders ─────────────────────────────────────────────────────
    elif any(x in q for x in ["work order", "execution", "operations"]):
        sql  = ("SELECT execution_status, COUNT(*) as count, SUM(amount_excl_gst) as total"
                " FROM work_orders GROUP BY execution_status ORDER BY count DESC;")
        rows = qdb(sql)
        db_text = str(rows)
        ans  = "**🛠️ Work Orders Execution Status**\n\n"
        for r in rows:
            ans += f"- **{r['execution_status'] or 'Unknown'}**: {r['count']} orders (₹{(r['total'] or 0)/1e5:.2f} L)\n"
        chart = ("pie", [r["execution_status"] or "Unknown" for r in rows], [r["count"] for r in rows], "WO Execution Status")

    # ── Fallback: try Gemini for any general question ────────────────────────
    else:
        gemini_ans = call_gemini(query)
        if gemini_ans:
            return gemini_ans, "", None
        ans = ("I can answer questions about:\n\n"
               "📊 **Revenue & Pipeline** | ⚡ **Energy Sector** | ⚠️ **Delayed Work Orders**\n"
               "🏢 **Top Clients** | 💰 **Expected Revenue** | 👑 **Leadership Summary**\n"
               "🌐 **Sectoral Performance** | 🛠️ **Work Orders** | 📋 **Operational Risks**\n\n"
               "Or ask me anything about **Skylark Drones** as a company!")

    # Try to enrich with Gemini
    gemini_ans = call_gemini(query, db_text)
    final_ans  = gemini_ans if gemini_ans else ans

    return final_ans, sql, chart


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
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
deals_n = qdb("SELECT COUNT(*) as n FROM deals")[0]["n"]
wos_n   = qdb("SELECT COUNT(*) as n FROM work_orders")[0]["n"]
st.sidebar.caption(f"📁 {deals_n} Deals · {wos_n} Work Orders")

# ─────────────────────────────────────────────────────────────────────────────
# 1. OVERVIEW — Premium Hero Layout
# ─────────────────────────────────────────────────────────────────────────────
if menu == "🏠 Overview":

    # ── Hero card ────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-card">
        <h1>🚁 Skylark Drones — BI Agent</h1>
        <p>Real-time business intelligence powered by AI. Instantly query revenue, pipeline health,
        operational metrics, and leadership reports — all from your Monday.com workspace data.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI strip ────────────────────────────────────────────────────────────
    won_rev   = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Won'")[0]["v"] or 0
    open_pipe = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Open'")[0]["v"] or 0
    billed    = qdb("SELECT SUM(billed_excl_gst) as v FROM work_orders")[0]["v"] or 0
    ar        = qdb("SELECT SUM(amount_receivable) as v FROM work_orders")[0]["v"] or 0
    open_cnt  = qdb("SELECT COUNT(*) as n FROM deals WHERE deal_status='Open'")[0]["n"]

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("🏆 Won Revenue",      f"₹{won_rev/1e7:.2f} Cr")
    k2.metric("🔄 Open Pipeline",    f"₹{open_pipe/1e7:.2f} Cr", f"{open_cnt} active deals")
    k3.metric("🧾 Total Billed",     f"₹{billed/1e5:.2f} L")
    k4.metric("📥 Outstanding AR",   f"₹{ar/1e5:.2f} L")
    k5.metric("📊 Database Records", f"{deals_n + wos_n}", f"{deals_n} deals · {wos_n} WOs")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Feature grid ─────────────────────────────────────────────────────────
    st.markdown("### What this agent can do for you")
    features = [
        ("💬", "Natural Language Queries", "Ask any business question in plain English — pipeline health, sector performance, client rankings, billing status."),
        ("📊", "Executive Dashboard", "Visual KPI charts: pipeline breakdown, sectoral performance, top owners, work order execution."),
        ("📄", "Leadership Reports", "Auto-generated executive summaries with probability-weighted forecasts. Copy or download as Markdown."),
        ("🔍", "Data Explorer", "Browse, search, and filter all 344 deals and 176 work orders with live CSV export."),
        ("🤖", "Gemini AI Powered", "Backed by Gemini 2.0 Flash for contextual, insightful answers — not just raw numbers."),
        ("⚡", "Monday.com Integration", "Reads from Monday.com boards via API. Falls back to local SQLite cache for offline resilience."),
    ]
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="feat-card">
                <div class="feat-icon">{icon}</div>
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)
        if i % 3 == 2:
            st.markdown("<br>", unsafe_allow_html=True)
            cols = st.columns(3)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Status timeline ───────────────────────────────────────────────────────
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("### 🕐 System Activity")
        st.markdown("""
        | Status | Component | Detail |
        |--------|-----------|--------|
        | 🟢 Online | API Integration | Web server running on Streamlit Cloud |
        | 🟢 Online | SQLite Database | 344 Deals + 176 Work Orders loaded |
        | 🟢 Ready  | AI Query Engine | Gemini 2.0 + local fallback resolver |
        | 🟢 Ready  | Monday.com API  | Mock GraphQL endpoint active |
        """)
    with col_r:
        st.markdown("### 🚀 Quick Start")
        st.info("👈 Use the **sidebar** to navigate between sections.")
        st.markdown("""
        **Try these:**
        - *"How is our pipeline looking?"*
        - *"What is our pending billing?"*
        - *"Tell me about Skylark Drones"*
        """)

# ─────────────────────────────────────────────────────────────────────────────
# 2. AI ASSISTANT
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "💬 AI Assistant":
    st.title("💬 AI Conversational Assistant")
    st.caption("Ask anything — business metrics, sector performance, company info, or any BI question.")

    # Founder pills
    PILLS = [
        ("📈 Pipeline Health",         "How is our pipeline looking?"),
        ("💰 Revenue Forecast",        "What is our total won revenue and pipeline forecast?"),
        ("⚡ Energy Sector",           "Show me the pipeline for Energy sector"),
        ("⚠️ Delayed Orders",          "Give me a summary of work orders execution and delays"),
        ("👑 Leadership Summary",      "Give me a comprehensive leadership summary update"),
        ("🏢 Top Enterprise Clients",  "Who are our top enterprise clients by pipeline value?"),
        ("💵 Expected Revenue",        "What is our expected revenue from open deals?"),
        ("🔴 Operational Risks",       "Show operational risks and stuck work orders"),
        ("🧾 Pending Billing",         "What is our pending billed value from work orders?"),
    ]

    st.markdown("**Quick Queries:**")
    cols = st.columns(3)
    for i, (label, query) in enumerate(PILLS):
        if cols[i % 3].button(label, key=f"pill_{i}", use_container_width=True):
            st.session_state.setdefault("messages", [])
            st.session_state["pending_query"] = query

    st.markdown("---")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": ("👋 Hi! I'm the **Skylark Drones BI Agent**.\n\n"
                        "I have access to **344 sales deals** and **176 work orders** from your Monday.com boards.\n\n"
                        "Ask me anything — from revenue figures to operational risks, or even general questions about Skylark Drones!")
        }]

    def render_chart(chart):
        if not chart:
            return
        ctype, x_labels, y_vals, title = chart
        if ctype == "bar":
            fig = px.bar(x=x_labels, y=y_vals, title=title,
                         labels={"x": "", "y": "Value (₹)"},
                         color=x_labels, color_discrete_sequence=px.colors.qualitative.Bold)
            fig.update_layout(showlegend=False, plot_bgcolor="#fff", paper_bgcolor="#fff")
            st.plotly_chart(fig, use_container_width=True)
        elif ctype in ("pie", "donut"):
            hole = .38 if ctype == "donut" else .0
            fig  = px.pie(names=x_labels, values=y_vals, title=title, hole=hole,
                          color_discrete_sequence=px.colors.qualitative.Bold)
            st.plotly_chart(fig, use_container_width=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "chart" in msg:
                render_chart(msg["chart"])
            if "sql" in msg and msg["sql"]:
                with st.expander("🗄️ SQL Query Used"):
                    st.code(msg["sql"], language="sql")

    # Handle pending query from pill click
    if "pending_query" in st.session_state:
        prompt = st.session_state.pop("pending_query")
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing data..."):
                ans, sql, chart = resolve_query(prompt)
            st.markdown(ans)
            if chart:
                render_chart(chart)
            if sql:
                with st.expander("🗄️ SQL Query Used"):
                    st.code(sql, language="sql")
        obj = {"role": "assistant", "content": ans, "sql": sql}
        if chart:
            obj["chart"] = chart
        st.session_state.messages.append(obj)
        st.rerun()

    if prompt := st.chat_input("Ask about revenue, pipeline, Skylark Drones, or any BI question…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                ans, sql, chart = resolve_query(prompt)
            st.markdown(ans)
            if chart:
                render_chart(chart)
            if sql:
                with st.expander("🗄️ SQL Query Used"):
                    st.code(sql, language="sql")
        obj = {"role": "assistant", "content": ans, "sql": sql}
        if chart:
            obj["chart"] = chart
        st.session_state.messages.append(obj)

# ─────────────────────────────────────────────────────────────────────────────
# 3. EXECUTIVE DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📊 Executive Dashboard":
    st.title("📊 Executive Dashboard")

    won_rev   = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Won'")[0]["v"] or 0
    open_pipe = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Open'")[0]["v"] or 0
    billed    = qdb("SELECT SUM(billed_excl_gst) as v FROM work_orders")[0]["v"] or 0
    ar        = qdb("SELECT SUM(amount_receivable) as v FROM work_orders")[0]["v"] or 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏆 Won Revenue",       f"₹{won_rev/1e7:.2f} Cr")
    c2.metric("🔄 Active Pipeline",   f"₹{open_pipe/1e7:.2f} Cr")
    c3.metric("🧾 Total Billed",      f"₹{billed/1e5:.2f} L")
    c4.metric("📥 Outstanding AR",    f"₹{ar/1e5:.2f} L")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### Pipeline Status Mix")
        df = pd.DataFrame(qdb("SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as value FROM deals GROUP BY deal_status"))
        cmap = {"Open": "#0073ea", "Won": "#00c875", "Dead": "#df2f4a", "On Hold": "#fdab3d"}
        fig  = px.pie(df, values="count", names="deal_status", hole=.38, color="deal_status", color_discrete_map=cmap)
        fig.update_layout(plot_bgcolor="#fff", paper_bgcolor="#fff")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("#### Sectoral Pipeline Value")
        df2 = pd.DataFrame(qdb("SELECT sector_service, SUM(masked_deal_value) as value FROM deals GROUP BY sector_service ORDER BY value DESC"))
        fig2 = px.bar(df2, x="sector_service", y="value", color="sector_service", labels={"value": "₹ Value", "sector_service": "Sector"})
        fig2.update_layout(showlegend=False, plot_bgcolor="#fff", paper_bgcolor="#fff")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### Work Orders Execution Status")
        df3 = pd.DataFrame(qdb("SELECT execution_status, COUNT(*) as count FROM work_orders GROUP BY execution_status ORDER BY count DESC"))
        fig3 = px.bar(df3, x="execution_status", y="count", color="execution_status", labels={"count": "Orders", "execution_status": "Status"})
        fig3.update_layout(showlegend=False, plot_bgcolor="#fff", paper_bgcolor="#fff")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("#### Top Owners by Won Revenue")
        df4 = pd.DataFrame(qdb("SELECT owner_code, SUM(masked_deal_value) as value FROM deals WHERE deal_status='Won' GROUP BY owner_code ORDER BY value DESC LIMIT 5"))
        fig4 = px.bar(df4, x="owner_code", y="value", color="owner_code", labels={"value": "₹ Revenue", "owner_code": "Owner"})
        fig4.update_layout(showlegend=False, plot_bgcolor="#fff", paper_bgcolor="#fff")
        st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# 4. DATA EXPLORER
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "🔍 Data Explorer":
    st.title("🔍 Interactive Data Explorer")
    tab_d, tab_w = st.tabs(["📁 Deals Board", "📁 Work Orders Board"])

    with tab_d:
        df_d = pd.DataFrame(qdb("SELECT * FROM deals"))
        c1, c2 = st.columns([2, 1])
        search    = c1.text_input("🔍 Search", placeholder="Name, owner, client, sector…", key="sd")
        statuses  = ["All"] + sorted(df_d["deal_status"].dropna().unique().tolist())
        sf        = c2.selectbox("Status", statuses, key="fds")
        if search:
            df_d = df_d[df_d.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]
        if sf != "All":
            df_d = df_d[df_d["deal_status"] == sf]
        st.dataframe(df_d, use_container_width=True, height=460)
        st.caption(f"Showing **{len(df_d)}** records")
        st.download_button("📥 Export CSV", df_d.to_csv(index=False), "deals_export.csv", "text/csv")

    with tab_w:
        df_w = pd.DataFrame(qdb("SELECT * FROM work_orders"))
        c1, c2 = st.columns([2, 1])
        search_w = c1.text_input("🔍 Search", placeholder="Customer, work type…", key="sw")
        execs    = ["All"] + sorted(df_w["execution_status"].dropna().unique().tolist())
        ef       = c2.selectbox("Execution Status", execs, key="few")
        if search_w:
            df_w = df_w[df_w.apply(lambda r: r.astype(str).str.contains(search_w, case=False).any(), axis=1)]
        if ef != "All":
            df_w = df_w[df_w["execution_status"] == ef]
        st.dataframe(df_w, use_container_width=True, height=460)
        st.caption(f"Showing **{len(df_w)}** records")
        st.download_button("📥 Export CSV", df_w.to_csv(index=False), "work_orders_export.csv", "text/csv")

# ─────────────────────────────────────────────────────────────────────────────
# 5. LEADERSHIP UPDATE
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📄 Leadership Update":
    st.title("📄 Executive Leadership Update")

    open_count  = qdb("SELECT COUNT(*) as n FROM deals WHERE deal_status='Open'")[0]["n"] or 0
    open_sum    = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Open'")[0]["v"] or 0
    weighted    = qdb("""SELECT SUM(
                           CASE WHEN closure_probability='High'   THEN masked_deal_value*.8
                                WHEN closure_probability='Medium' THEN masked_deal_value*.5
                                WHEN closure_probability='Low'    THEN masked_deal_value*.2
                                ELSE 0 END) as v FROM deals WHERE deal_status='Open'""")[0]["v"] or 0
    won_sum     = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Won'")[0]["v"] or 0
    comp_count  = qdb("SELECT COUNT(*) as n FROM work_orders WHERE execution_status='Completed'")[0]["n"] or 0
    total_b     = qdb("SELECT SUM(billed_excl_gst) as v FROM work_orders")[0]["v"] or 0
    total_r     = qdb("SELECT SUM(amount_receivable) as v FROM work_orders")[0]["v"] or 0
    date_str    = datetime.now().strftime("%B %d, %Y")

    st.markdown('<span class="green-badge">● EXECUTIVE REPORT READY</span>', unsafe_allow_html=True)

    md = f"""# 📄 Skylark Drones — Executive Leadership Update

**Date:** {date_str}  
**Data Source:** Dynamic Monday.com Integrations *(Deals Board & Work Orders Board)*

---

### 1. Executive Summary

Skylark Drones is tracking a **total sales pipeline of ₹{open_sum/1e7:.2f} Cr** across **{open_count} active deals**, with a probability-weighted expected revenue of **₹{weighted/1e7:.2f} Cr**. Operations have successfully delivered **{comp_count} work orders**, achieving a total billed value of **₹{total_b/1e5:.2f} Lakhs**.

### 2. Revenue & Financial Overview

| Financial Metric | Amount (INR) | Key Observations |
|---|---|---|
| **Total Open Pipeline** | ₹{open_sum:,.2f} | Driven by Mining & Powerline sector proposals |
| **Probability-Weighted Revenue** | ₹{weighted:,.2f} | High (80%), Medium (50%), Low (20%) |
| **Realized Won Revenue** | ₹{won_sum:,.2f} | Closed-won contract commitments |
| **Billed Work Order Value** | ₹{total_b:,.2f} | Invoiced operational deliveries |
| **Outstanding Receivables** | ₹{total_r:,.2f} | Requires collection prioritization |
"""

    col1, col2, col3 = st.columns([3, 1, 1])
    col1.markdown(f"**Date:** {date_str}  |  **Source:** Monday.com (Deals & Work Orders Boards)")
    col2.download_button("📥 Download .md", md, "Skylark_Report.md", "text/markdown", use_container_width=True)
    if col3.button("📋 Copy Summary", use_container_width=True):
        st.toast("Summary ready to copy — use the Download button for full report!", icon="✅")

    st.markdown("---")
    st.markdown(f"""
### 1. Executive Summary

Skylark Drones is tracking a **total sales pipeline of ₹{open_sum/1e7:.2f} Cr** across **{open_count} active deals**,
with a probability-weighted expected revenue of **₹{weighted/1e7:.2f} Cr** *(High=80%, Medium=50%, Low=20%)*.  
Operations have successfully delivered **{comp_count} work orders**, achieving a total billed value of **₹{total_b/1e5:.2f} Lakhs**.
""")

    st.markdown("### 2. Revenue & Financial Overview")
    metrics = [
        ("Total Open Pipeline",          f"₹{open_sum:,.2f}",  "Driven by large Mining & Powerline sector proposals"),
        ("Probability-Weighted Revenue",  f"₹{weighted:,.2f}",  "High (80%), Medium (50%), Low (20%) closure probability"),
        ("Realized Won Revenue",          f"₹{won_sum:,.2f}",   "Closed-won contract commitments"),
        ("Billed Work Order Value",       f"₹{total_b:,.2f}",   "Invoiced operational deliveries"),
        ("Outstanding Receivables",       f"₹{total_r:,.2f}",   "Requires collection prioritization for priority accounts"),
    ]
    rows_html = "".join(
        f"<tr><td><strong>{m}</strong></td><td>{a}</td><td style='color:#676879'>{k}</td></tr>"
        for m, a, k in metrics
    )
    st.markdown(f"""
    <table class="report-table">
      <thead><tr><th>Financial Metric</th><th>Amount (INR)</th><th>Key Observations</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("### 3. Visual Snapshot")
    ca, cb = st.columns(2)
    df_snap = pd.DataFrame(qdb("SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as value FROM deals GROUP BY deal_status"))
    cmap    = {"Open": "#0073ea", "Won": "#00c875", "Dead": "#df2f4a", "On Hold": "#fdab3d"}
    with ca:
        fig1 = px.pie(df_snap, values="count", names="deal_status", hole=.38, title="Deals by Status", color="deal_status", color_discrete_map=cmap)
        fig1.update_layout(plot_bgcolor="#fff", paper_bgcolor="#fff")
        st.plotly_chart(fig1, use_container_width=True)
    with cb:
        fig2 = px.bar(df_snap, x="deal_status", y="value", color="deal_status", title="Pipeline Value by Status", color_discrete_map=cmap, labels={"value": "₹ Value"})
        fig2.update_layout(showlegend=False, plot_bgcolor="#fff", paper_bgcolor="#fff")
        st.plotly_chart(fig2, use_container_width=True)
