import os
import sys
import json
import urllib.request
import urllib.error
import re
from backend.database import query_db

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Standard system prompt defining database structure
SCHEMA_PROMPT = """
You are an expert SQL assistant for a Monday.com Business Intelligence Agent.
The SQLite database contains two tables:
1. `deals` with columns:
   - deal_name (text)
   - owner_code (text)
   - client_code (text)
   - deal_status (text: 'Open', 'Won', 'Dead', 'On Hold')
   - close_date_actual (text: YYYY-MM-DD or empty)
   - closure_probability (text: 'High', 'Medium', 'Low')
   - masked_deal_value (real)
   - tentative_close_date (text: YYYY-MM-DD or empty)
   - deal_stage (text: 'A. Lead Generated', 'B. Sales Qualified Leads', 'C. Demo Done', 'D. Feasibility', 'E. Proposal/Commercials Sent', 'F. Negotiations', 'G. Project Won', 'H. Work Order Received', 'I. POC', 'J. Invoice sent', 'K. Amount Accrued', 'L. Project Lost', 'M. Projects On Hold', 'O. Not Relevant at all')
   - product_deal (text)
   - sector_service (text: 'Mining', 'Powerline', 'Renewables', 'Railways', 'Construction', 'Tender', 'DSP', 'Aviation', 'Others')
   - created_date (text)

2. `work_orders` with columns:
   - deal_name_masked (text)
   - customer_name_code (text)
   - serial_num (text)
   - nature_of_work (text)
   - last_executed_month (text)
   - execution_status (text: 'Completed', 'Ongoing', 'Not Started', 'Executed until current month', 'Partial Completed', 'Pause / struck')
   - data_delivery_date (text)
   - date_of_po_loi (text)
   - document_type (text)
   - probable_start_date (text)
   - probable_end_date (text)
   - bd_kam_personnel_code (text)
   - sector (text)
   - type_of_work (text)
   - is_skylark_platform_deliverable (text: 'NONE', 'SPECTRA', 'DMO', 'SPECTRA + DMO')
   - last_invoice_date (text)
   - latest_invoice_num (text)
   - amount_excl_gst (real)
   - amount_incl_gst (real)
   - billed_excl_gst (real)
   - billed_incl_gst (real)
   - collected_incl_gst (real)
   - amount_receivable (real)
   - ar_priority_account (text)
   - quantity_by_ops (real)
   - quantities_as_per_po (text)
   - quantity_billed_till_date (real)
   - balance_in_quantity (real)
   - invoice_status (text: 'Fully Billed', 'Partially Billed', 'Not billed yet', 'Stuck', 'Billed- Visit 3', 'Billed- Visit 7')
   - expected_billing_month (text)
   - actual_billing_month (text)
   - actual_collection_month (text)
   - wo_status_billed (text)
   - collection_status (text)
   - collection_date (text)
   - billing_status (text: 'Billed', 'Not Billable', 'Partially Billed', 'Update Required', 'Stuck')

Given the user query, output ONLY a clean SQLite SQL query that fetches the necessary data to answer the question. Do not include markdown formatting or backticks around the SQL query. Output just the raw SQL query.
"""

def call_gemini(prompt):
    """Calls the Gemini generateContent API via urllib."""
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key is not set.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode("utf-8"), 
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            res_json = json.loads(res.read().decode("utf-8"))
            text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
    except urllib.error.URLError as e:
        raise Exception(f"Gemini API connection error: {e}")

def resolve_query_gemini(query):
    """Uses Gemini LLM to write and answer the SQL query."""
    # Step 1: Text-to-SQL
    sql_prompt = f"{SCHEMA_PROMPT}\nUser Query: {query}"
    sql = call_gemini(sql_prompt)
    
    # Strip any formatting/markdown blocks if Gemini returned them
    sql = sql.replace("```sql", "").replace("```", "").strip()
    # Remove leading/trailing quotes
    if sql.startswith('"') and sql.endswith('"'):
        sql = sql[1:-1]
        
    print(f"Agent generated SQL: {sql}", file=sys.stderr)
    
    # Step 2: Execute SQL
    data = query_db(sql)
    print(f"Data retrieved: {len(data)} rows", file=sys.stderr)
    
    # Step 3: Synthesize Answer
    synthesis_prompt = f"""
    You are the Monday.com Business Intelligence Agent.
    
    User Query: "{query}"
    SQL Query Executed: "{sql}"
    Data Retrieved: {json.dumps(data[:30], indent=2)} (total rows: {len(data)})
    
    Provide a professional, conversational response summarizing the data. Include key business insights and point out any data anomalies or caveats (such as null/missing fields, outliers, negative receivable values, etc.).
    
    If the data is suitable for visualization (e.g. breakdown of pipeline values, counts, timelines), append a JSON chart configuration at the very end of your response inside a ```chart code block. The JSON format must strictly be:
    {{
      "type": "bar" | "pie" | "line" | "doughnut",
      "labels": ["Label1", "Label2", ...],
      "datasets": [
        {{
          "label": "Dataset Label",
          "data": [Value1, Value2, ...]
        }}
      ]
    }}
    Do not add extra fields in the chart JSON.
    """
    answer = call_gemini(synthesis_prompt)
    return answer, sql

def resolve_query_fallback(query):
    """Fallback rule-based query parser in case Gemini is offline or key is missing."""
    q = query.lower()
    sql = ""
    ans = ""
    chart = None
    owner_code = None
    client_code = None
    serial_num = None
    
    # 1. Check for Pending Billing explicitly
    if "pending billing" in q or "pending billed" in q:
        sql = "SELECT SUM(amount_excl_gst) as total_po, SUM(billed_excl_gst) as total_billed, SUM(CASE WHEN amount_excl_gst > billed_excl_gst THEN amount_excl_gst - billed_excl_gst ELSE 0 END) as pending_billing FROM work_orders;"
        data = query_db(sql)
        po = data[0]['total_po'] or 0
        billed = data[0]['total_billed'] or 0
        pending = data[0]['pending_billing'] or 0
        ans = f"### 📊 Work Orders Pending Billing Summary\n\n"
        ans += f"Here is the billing status summary for all executed work orders:\n\n"
        ans += f"● **Total PO Contract Value (Excl GST)**: ₹{po:,.2f}\n"
        ans += f"● **Total Billed to Date (Excl GST)**: ₹{billed:,.2f}\n"
        ans += f"● **Pending Billing Amount (Remaining PO Balance)**: **₹{pending:,.2f}**\n\n"
        ans += f"ℹ️ *Note: The pending billing amount represents the remaining balance on work orders where the contracted PO value exceeds the amount billed to date. Messy records with over-billing offsets have been adjusted to zero to ensure metrics accuracy.*"
        chart = {
            "type": "bar",
            "labels": ["Billed Value", "Pending Billing"],
            "datasets": [{"label": "Amount (₹)", "data": [billed, pending]}]
        }

    # 2. Check for Revenue Forecast explicitly
    elif "revenue forecast" in q or "pipeline forecast" in q or "forecast" in q:
        sql = """
        SELECT 
            SUM(CASE WHEN deal_status = 'Won' THEN masked_deal_value ELSE 0 END) as won_revenue,
            SUM(CASE WHEN deal_status = 'Open' THEN masked_deal_value ELSE 0 END) as open_pipeline,
            SUM(CASE WHEN deal_status = 'Open' AND closure_probability = 'High' THEN masked_deal_value * 0.8 
                     WHEN deal_status = 'Open' AND closure_probability = 'Medium' THEN masked_deal_value * 0.5 
                     WHEN deal_status = 'Open' AND closure_probability = 'Low' THEN masked_deal_value * 0.2 
                     ELSE 0 END) as weighted_forecast
        FROM deals;
        """
        data = query_db(sql)
        won = data[0]['won_revenue'] or 0
        open_val = data[0]['open_pipeline'] or 0
        weighted = data[0]['weighted_forecast'] or 0
        ans = f"### 📈 Revenue & Pipeline Forecast Summary\n\n"
        ans += f"Here is our sales revenue forecast based on active deals in the pipeline:\n\n"
        ans += f"● **Won Revenue**: ₹{won:,.2f} (100% realized)\n"
        ans += f"● **Total Open Pipeline Value**: ₹{open_val:,.2f} (outstanding pipeline)\n"
        ans += f"● **Weighted Pipeline Forecast**: **₹{weighted:,.2f}** (probability-adjusted expected revenue)\n\n"
        ans += f"● **Total Projected Revenue (Won + Forecast)**: **₹{won + weighted:,.2f}**\n"
        chart = {
            "type": "bar",
            "labels": ["Won Revenue", "Open Pipeline", "Weighted Forecast"],
            "datasets": [{"label": "Value (₹)", "data": [won, open_val, weighted]}]
        }

    # 3. Check for Delayed Work Orders explicitly
    elif "delayed work" in q or "delays" in q:
        sql = "SELECT execution_status, COUNT(*) as count, SUM(amount_excl_gst) as total_value FROM work_orders WHERE execution_status IN ('Not Started', 'Pause / struck') GROUP BY execution_status;"
        data = query_db(sql)
        ans = f"### ⚠️ Delayed and At-Risk Work Orders\n\n"
        ans += f"Here is the breakdown of work orders that are currently delayed or have not started:\n\n"
        total_risk_val = 0
        labels, vals = [], []
        for r in data:
            status = r['execution_status'] or 'Unknown'
            val = r['total_value'] or 0
            ans += f"● **{status}**: {r['count']} work orders (Total Value: ₹{val:,.2f})\n"
            total_risk_val += val
            labels.append(status)
            vals.append(val)
        ans += f"\n● **Total Backlog/At-Risk Value**: **₹{total_risk_val:,.2f}**\n"
        chart = {
            "type": "pie",
            "labels": labels,
            "datasets": [{"label": "At-Risk Value", "data": vals}]
        }

    # 4. Check for Leadership Summary explicitly
    elif "leadership summary" in q or "comprehensive leadership" in q:
        sql = """
        SELECT 
            (SELECT SUM(masked_deal_value) FROM deals WHERE deal_status = 'Won') as total_revenue,
            (SELECT COUNT(*) FROM deals WHERE deal_status = 'Open') as open_deals_count,
            (SELECT SUM(masked_deal_value) FROM deals WHERE deal_status = 'Open') as open_pipeline,
            (SELECT SUM(amount_excl_gst) FROM work_orders WHERE execution_status = 'Completed') as completed_work_value,
            (SELECT SUM(amount_receivable) FROM work_orders) as total_receivable
        FROM deals LIMIT 1;
        """
        data = query_db(sql)
        rev = data[0]['total_revenue'] or 0
        open_count = data[0]['open_deals_count'] or 0
        open_pipe = data[0]['open_pipeline'] or 0
        completed = data[0]['completed_work_value'] or 0
        rec = data[0]['total_receivable'] or 0
        ans = f"### 👑 Executive Leadership Summary Update\n\n"
        ans += f"Here is a comprehensive summary of our business health across sales and operations:\n\n"
        ans += f"#### 💼 Sales & Pipeline Performance\n"
        ans += f"● **Total Billed Sales Revenue (Won)**: ₹{rev:,.2f}\n"
        ans += f"● **Active Sales Pipeline**: ₹{open_pipe:,.2f} across {open_count} open deals\n\n"
        ans += f"#### 🛠️ Operations & Financial Outstanding\n"
        ans += f"● **Completed Project Value**: ₹{completed:,.2f}\n"
        ans += f"● **Outstanding Account Receivables (AR)**: ₹{rec:,.2f}\n"

    # 5. Check for Top Enterprise Clients explicitly
    elif "enterprise client" in q or "top enterprise" in q:
        sql = "SELECT client_code, SUM(masked_deal_value) as total_value, COUNT(*) as count FROM deals GROUP BY client_code ORDER BY total_value DESC LIMIT 5;"
        data = query_db(sql)
        ans = f"### 🏢 Top Enterprise Clients by Pipeline Value\n\n"
        ans += f"Here are our top 5 enterprise clients ranked by active pipeline value:\n\n"
        labels, vals = [], []
        for i, r in enumerate(data, 1):
            val = r['total_value'] or 0
            ans += f"{i}. **{r['client_code']}**: ₹{val:,.2f} ({r['count']} deals)\n"
            labels.append(r['client_code'])
            vals.append(val)
        chart = {
            "type": "bar",
            "labels": labels,
            "datasets": [{"label": "Pipeline Value (₹)", "data": vals}]
        }

    # 6. Check for Expected Revenue explicitly
    elif "expected revenue" in q:
        sql = """
        SELECT 
            SUM(masked_deal_value) as total_open,
            SUM(CASE WHEN closure_probability = 'High' THEN masked_deal_value * 0.8 
                     WHEN closure_probability = 'Medium' THEN masked_deal_value * 0.5 
                     WHEN closure_probability = 'Low' THEN masked_deal_value * 0.2 
                     ELSE 0 END) as expected
        FROM deals WHERE deal_status = 'Open';
        """
        data = query_db(sql)
        total = data[0]['total_open'] or 0
        expected = data[0]['expected'] or 0
        ans = f"### 💰 Expected Revenue Forecast from Open Deals\n\n"
        ans += f"Expected revenue is calculated by applying closure probabilities (High: 80%, Medium: 50%, Low: 20%) to active pipeline values:\n\n"
        ans += f"● **Total Open Pipeline Value**: ₹{total:,.2f}\n"
        ans += f"● **Expected (Probability-Adjusted) Revenue**: **₹{expected:,.2f}**\n"
        chart = {
            "type": "doughnut",
            "labels": ["Expected Value", "Risk Discount"],
            "datasets": [{"label": "Value (₹)", "data": [expected, total - expected]}]
        }

    # 7. Check for Operational Risks explicitly
    elif "operational risk" in q or "stuck work" in q or "risks" in q:
        sql = "SELECT serial_num, customer_name_code, nature_of_work, amount_excl_gst, execution_status FROM work_orders WHERE execution_status = 'Pause / struck' OR billing_status = 'Stuck' LIMIT 5;"
        data = query_db(sql)
        ans = f"### ⚡ Operational Risks & Stuck Projects\n\n"
        ans += f"Here are the top active project execution risks (paused work orders or stuck billing):\n\n"
        for r in data:
            val = r['amount_excl_gst'] or 0
            ans += f"● **{r['serial_num']}** ({r['customer_name_code']}): {r['nature_of_work']} ➔ **{r['execution_status']}** (Value: ₹{val:,.2f})\n"

    # 8. Check for specific Energy Sector pipeline
    elif "energy sector" in q or "energy" in q:
        sql = "SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as total_value FROM deals WHERE LOWER(sector_service) IN ('powerline', 'renewables') GROUP BY deal_status;"
        data = query_db(sql)
        ans = f"### ⚡ Energy Sector Sales Pipeline Performance\n\n"
        ans += f"Here is the pipeline status summary for the Energy sector (Powerline and Renewables lines of business):\n\n"
        labels, vals = [], []
        for r in data:
            status = r['deal_status'] or 'Unknown'
            val = r['total_value'] or 0
            ans += f"● **{status}**: {r['count']} deals (Value: ₹{val:,.2f})\n"
            labels.append(status)
            vals.append(val)
        chart = {
            "type": "doughnut",
            "labels": labels,
            "datasets": [{"label": "Energy Pipeline", "data": vals}]
        }

    else:
        # Extract owner codes if present (e.g. owner_001, owner_002, etc.)
        owner_match = re.search(r"owner_?\d+", q)
        owner_code = owner_match.group(0).upper() if owner_match else None
        if owner_match and "OWNER_" not in owner_code:
            owner_code = owner_code.replace("OWNER", "OWNER_")
        
        # Extract client codes if present (e.g. company124, company089, etc.)
        client_match = re.search(r"company\d+", q)
        client_code = client_match.group(0).upper() if client_match else None
        
        # Extract serial numbers if present (e.g. sdpldeal-075)
        serial_match = re.search(r"sdpldeal-\d+", q)
        serial_num = serial_match.group(0).upper() if serial_match else None

    if ans:
        if chart:
            ans += f"\n\n```chart\n{json.dumps(chart, indent=2)}\n```"
        return ans, sql

    # Check for specific serial number query first
    if serial_num:
        sql = f"SELECT * FROM work_orders WHERE UPPER(serial_num) = '{serial_num}';"
        data = query_db(sql)
        if data:
            row = data[0]
            ans = f"Here are the work order details for serial number **{serial_num}**:\n\n"
            ans += f"● **Deal name**: {row['deal_name_masked']}\n"
            ans += f"● **Customer**: {row['customer_name_code']}\n"
            ans += f"● **Nature of Work**: {row['nature_of_work']}\n"
            ans += f"● **Execution Status**: {row['execution_status']}\n"
            ans += f"● **Billed Value (Excl GST)**: ₹{row['billed_excl_gst'] or 0:,.2f}\n"
            ans += f"● **Amount Receivable**: ₹{row['amount_receivable'] or 0:,.2f}\n"
            ans += f"● **Billing Status**: {row['billing_status']}\n"
        else:
            ans = f"No work order found with serial number **{serial_num}**."
            
    # Check for specific client query
    elif client_code:
        if "work order" in q or "project" in q or "billed" in q:
            sql = f"SELECT serial_num, nature_of_work, execution_status, amount_excl_gst FROM work_orders WHERE UPPER(customer_name_code) = '{client_code}';"
            data = query_db(sql)
            if data:
                ans = f"Here are the work orders for client **{client_code}**:\n\n"
                for r in data:
                    ans += f"● **{r['serial_num']}** ({r['nature_of_work']}): {r['execution_status']} (Amount: ₹{r['amount_excl_gst'] or 0:,.2f})\n"
            else:
                ans = f"No work orders found for client **{client_code}**."
        else:
            sql = f"SELECT deal_name, deal_status, masked_deal_value, deal_stage FROM deals WHERE UPPER(client_code) = '{client_code}';"
            data = query_db(sql)
            if data:
                ans = f"Here are the deals associated with client **{client_code}**:\n\n"
                for r in data:
                    val = r['masked_deal_value'] or 0
                    ans += f"● **{r['deal_name']}**: Status is **{r['deal_status']}** (Value: ₹{val:,.2f}) at stage {r['deal_stage']}\n"
            else:
                ans = f"No deals found for client **{client_code}**."
                
    # Check for specific owner query
    elif owner_code:
        status_filter = ""
        status_title = "all"
        if "won" in q or "revenue" in q:
            status_filter = " AND deal_status = 'Won'"
            status_title = "Won"
        elif "open" in q or "pipeline" in q:
            status_filter = " AND deal_status = 'Open'"
            status_title = "Open"
            
        sql = f"SELECT deal_name, deal_status, masked_deal_value, client_code FROM deals WHERE UPPER(owner_code) = '{owner_code}'{status_filter};"
        data = query_db(sql)
        if data:
            ans = f"Here are the {status_title} deals managed by owner **{owner_code}**:\n\n"
            labels, vals = [], []
            for r in data:
                val = r['masked_deal_value'] or 0
                ans += f"● **{r['deal_name']}** (Client: {r['client_code']}): ₹{val:,.2f} ({r['deal_status']})\n"
                labels.append(r['deal_name'])
                vals.append(val)
            if len(data) > 1:
                chart = {
                    "type": "bar",
                    "labels": labels[:10],
                    "datasets": [{"label": "Deal Value", "data": vals[:10]}]
                }
        else:
            ans = f"No {status_title} deals found for owner **{owner_code}**."
            
    # Check for specific sector query
    elif "sector" in q or "mining" in q or "renewables" in q or "powerline" in q or "railways" in q or "aviation" in q or "tender" in q:
        target_sector = None
        for sec in ["mining", "powerline", "renewables", "railways", "construction", "tender", "dsp", "aviation"]:
            if sec in q:
                target_sector = sec.capitalize()
                break
                
        if target_sector:
            sql = f"SELECT deal_status, SUM(masked_deal_value) as value, COUNT(*) as count FROM deals WHERE LOWER(sector_service) = '{target_sector.lower()}' GROUP BY deal_status;"
            data = query_db(sql)
            ans = f"Here is the pipeline status specifically for the **{target_sector}** sector:\n\n"
            labels, vals = [], []
            for r in data:
                status = r["deal_status"] or "Unknown"
                val = r["value"] or 0
                ans += f"● **{status}**: {r['count']} deals (Value: ₹{val:,.2f})\n"
                labels.append(status)
                vals.append(val)
            chart = {
                "type": "doughnut",
                "labels": labels,
                "datasets": [{"label": f"{target_sector} Pipeline", "data": vals}]
            }
        else:
            sql = "SELECT sector_service, SUM(masked_deal_value) as value FROM deals GROUP BY sector_service ORDER BY value DESC;"
            data = query_db(sql)
            ans = "Here is the performance/pipeline value across different sectors:\n\n"
            labels, vals = [], []
            for r in data:
                sector = r["sector_service"] or "Other/Unknown"
                val = r["value"] or 0
                ans += f"● **{sector}**: ₹{val:,.2f}\n"
                labels.append(sector)
                vals.append(val)
            chart = {
                "type": "bar",
                "labels": labels,
                "datasets": [{"label": "Pipeline Value by Sector", "data": vals}]
            }
            
    # Check for pipeline health overview
    elif "pipeline" in q or "health" in q or "status" in q or "overview" in q:
        sql = "SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as total_value FROM deals GROUP BY deal_status;"
        data = query_db(sql)
        ans = "Here is an overview of the sales pipeline status and values:\n\n"
        labels, vals = [], []
        for r in data:
            status = r["deal_status"] or "Unknown"
            count = r["count"]
            val = r["total_value"] or 0
            ans += f"● **{status}**: {count} deals (Total Value: ₹{val:,.2f})\n"
            labels.append(status)
            vals.append(val)
        chart = {
            "type": "pie",
            "labels": labels,
            "datasets": [{"label": "Pipeline Value", "data": vals}]
        }
        
    # Check for billing / work order summaries
    elif "work order" in q or "execution" in q or "billed" in q or "invoice" in q:
        sql = "SELECT execution_status, COUNT(*) as count, SUM(amount_excl_gst) as total_amount FROM work_orders GROUP BY execution_status;"
        data = query_db(sql)
        ans = "Here is the summary of work orders execution status:\n\n"
        labels, vals = [], []
        for r in data:
            status = r["execution_status"] or "Unknown"
            amt = r["total_amount"] or 0
            ans += f"● **{status}**: {r['count']} work orders (Amount: ₹{amt:,.2f})\n"
            labels.append(status)
            vals.append(amt)
        chart = {
            "type": "bar",
            "labels": labels,
            "datasets": [{"label": "Work Order Value", "data": vals}]
        }
        
    # Check for top owners ranking
    elif "top" in q or "owner" in q or "salesperson" in q or "performer" in q:
        sql = "SELECT owner_code, SUM(masked_deal_value) as value FROM deals WHERE deal_status='Won' GROUP BY owner_code ORDER BY value DESC LIMIT 5;"
        data = query_db(sql)
        ans = "Here are the top performing owners/salespeople based on Won deals:\n\n"
        labels, vals = [], []
        for r in data:
            owner = r["owner_code"] or "Unknown"
            val = r["value"] or 0
            ans += f"● **{owner}**: ₹{val:,.2f} in revenue\n"
            labels.append(owner)
            vals.append(val)
        chart = {
            "type": "bar",
            "labels": labels,
            "datasets": [{"label": "Revenue Won", "data": vals}]
        }

    # If it is just a general question about total deals or won deals
    elif "won" in q or "revenue" in q:
        sql = "SELECT SUM(masked_deal_value) as total_revenue, COUNT(*) as count FROM deals WHERE deal_status='Won';"
        data = query_db(sql)
        ans = f"Our total won revenue is **₹{data[0]['total_revenue'] or 0:,.2f}** from **{data[0]['count']} won deals**."
        
    elif "open" in q or "deal" in q:
        sql = "SELECT SUM(masked_deal_value) as total_value, COUNT(*) as count FROM deals WHERE deal_status='Open';"
        data = query_db(sql)
        ans = f"We currently have **{data[0]['count']} open deals** in our pipeline, with an active pipeline value of **₹{data[0]['total_value'] or 0:,.2f}**."

    # Default fallback welcome message
    else:
        sql = "SELECT COUNT(*) as count FROM deals;"
        data = query_db(sql)
        ans = f"Welcome to the Skylark BI chatbot! I've loaded the local SQLite database containing {data[0]['count']} deals and 176 work orders. You can ask queries like:\n"
        ans += "1. *'Show pipeline overview'* \n"
        ans += "2. *'How is the pipeline looking for energy/mining sector?'* \n"
        ans += "3. *'Who is the top owner by revenue?'* \n"
        ans += "4. *'Give me a summary of work orders execution'* \n"
        ans += "5. *'Show details for serial number SDPLDEAL-075'* \n"
        ans += "6. *'List all open deals for OWNER_001'* \n"
        ans += "7. *'What are the deals for COMPANY124?'* \n"
        
    if chart:
        ans += f"\n\n```chart\n{json.dumps(chart, indent=2)}\n```"
        
    return ans, sql

def ask_agent(query):
    """Public interface to query the agent."""
    if GEMINI_API_KEY:
        try:
            return resolve_query_gemini(query)
        except Exception as e:
            print(f"Gemini resolution failed, falling back: {e}", file=sys.stderr)
            return resolve_query_fallback(query)
    else:
        print("No Gemini API key found. Using fallback rule-based resolver.", file=sys.stderr)
        return resolve_query_fallback(query)
