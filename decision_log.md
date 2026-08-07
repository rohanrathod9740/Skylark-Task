# Decision Log - Monday.com Business Intelligence Agent

## 1. Key Assumptions & Data Resilience Decisions

### A. Reconstructing Split Tables from Messy PDFs
* **Assumption**: The provided PDF files (`media__1786087595640.pdf` and `media__1786087595661.pdf`) represent horizontal slices of tables (Deals and Work Orders) split across page boundaries. 
* **Design Decision**: In `reconstruct_data.py`, we assumed a strict vertical row alignment based on index order (e.g. Row 1 on page 1 matches Row 1 on page 10). We built a coordinate-tolerant vertical cell parsing pipeline using `pdfplumber` that maps column headers, merges horizontal rows across pages, and handles missing/overlapping coordinates. 
* **Result**: Generated fully merged `deals_data.csv` (344 records) and `work_orders_data.csv` (176 records) without losing row indices.

### B. Inconsistent Data Formats & Financial Anomalies
* **Decisions**: 
  - **Financial values**: We handled commas, currency symbols, and spaces via clean regular expressions.
  - **Negative value offsets**: For work orders where billed value exceeded the PO value (indicating over-billing or data errors), we implemented a floor check: `CASE WHEN billed_excl_gst > amount_excl_gst THEN 0 ELSE amount_excl_gst - billed_excl_gst END` to prevent negative values from distorting aggregate BI forecasts.
  - **Date Normalization**: Dates were represented inconsistently (e.g., `YYYY-MM-DD`, `DD/MM/YY`, or month names). We normalized them into standard `YYYY-MM-DD` strings for reliable date sorting in SQLite, falling back to original strings where parsing failed.

---

## 2. Technical Architecture Trade-offs

### A. Streamlit (Python) vs. Node.js (Express) Hybrid Frameworks
* **Trade-off**: Build exclusively in one language or provide a hybrid model.
* **Decision**: We implemented both a **self-contained Streamlit Cloud Python app** and a **Node.js Express + Python child process architecture** locally.
* **Rationale**: Streamlit Cloud is the industry standard for fast, high-performance executive dashboards, but local sandboxes occasionally fail to download packages due to strict network configurations. The Node.js Express server runs on standard vanilla JS with native SQLite bindings, ensuring that if a recruiter runs it locally via `npm start`, the app is guaranteed to launch without dependency install issues.

### B. SQLite Database Caching Layer
* **Trade-off**: Query Monday.com API directly vs. querying a local database cache.
* **Decision**: SQLite cache layer (`backend/skylark.db`).
* **Rationale**: Direct Monday.com API calls are subject to rate limiting, network latency, and authentication checks. By loading reconstructed CSV data into SQLite, the AI agent can execute high-speed query operations (sorting, joining, filtering) in milliseconds. If real Monday.com API keys are supplied, the cache is automatically populated with fresh data via GraphQL.

### C. Rule-Based Fallback vs. AI Text-to-SQL Resolver
* **Trade-off**: Relying solely on AI SQL generation vs. hardcoded query templates.
* **Decision**: We built a **hybrid dual-engine routing model**:
  - **AI Text-to-SQL Engine**: Enabled when `GEMINI_API_KEY` is present. It asks Gemini to translate queries to SQLite, sanitizes them for safety, runs them, and summarizes results with Plotly visualizations.
  - **Rule-Based Fallback Engine**: If Gemini is offline, a keyword/regex-based engine processes all 9 founder-level queries locally. This ensures 100% reliability.

---

## 3. SQL Safety Guardrails (Security)
* **Risk**: Natural-language-to-SQL execution invites SQL injection or destructive queries (e.g. `DROP TABLE`, `DELETE FROM`).
* **Implementation**: We implemented a rigorous safety validator (`is_safe_sql`) that blocks any non-`SELECT` statements and searches for SQL command keywords using boundary-bounded regexes (`\bDROP\b`, `\bDELETE\b`, etc.). Any unsafe query is rejected immediately, falling back to the local resolver.

---

## 4. Interpretation of "Leadership Updates"
To provide maximum business value to a founder, we interpreted "Leadership Updates" in four distinct layers:
1. **Dynamic Markdown Executive Summary**: A dedicated page compiles active pipeline totals, realized won revenue, completed project metrics, and outstanding receivables into a professional report. Founders can copy this text or download it as a `.md` file for company updates.
2. **Interactive Visual Dashboard**: A visually striking dashboard detailing Pipeline status mix, Sectoral pipeline value, Work Order execution rates, and Owner revenue leaderboards.
3. **Proactive AI Recommendations**: The AI Agent appends confidence ratings, anomaly alerts, and actionable recommendations to answers (e.g. flagging outstanding priority receivables).
4. **Conversational Charting**: The AI Agent automatically attaches appropriate Plotly configs (bar/pie/donut) to answer summaries, enabling direct visual chart rendering in the chat thread.
