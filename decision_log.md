# Decision Log - Monday.com Business Intelligence Agent

## 1. Key Assumptions Made

* **PDF Data Alignment**: The provided PDFs (`media__1786087595640.pdf` and `media__1786087595661.pdf`) represent "Deals" and "Work Orders" tables split horizontally across multiple page sets. We assumed the data rows align 1-to-1 vertically in structural page index order (e.g. data row 1 on Page 1 aligns with data row 1 on Page 10 of the Deals PDF). Our parser successfully aligned these to reconstruct 344 Deals and 176 Work Orders.
* **API Key Offline Fallback**: Since internet access may be restricted or API keys may be absent in the user's sandbox environment, we assumed the agent must work out-of-the-box in a mock configuration. The system falls back automatically to a local query engine using SQLite if the Monday.com API key is not supplied or is set to `mock`.
* **Heuristic Query Engine Fallback**: If the Google Gemini API key is missing or calls fail due to DNS/network timeouts, we assumed the system must fall back to a rule-based/regex query parser mapping basic requests (such as pipeline overview, top owners, sectoral performance) to predefined SQL statements. This ensures the app is highly resilient.

## 2. Key Technical Trade-offs Chosen

### A. Full Stack: Node.js Express + Python Hybrid Architecture
* **Trade-off**: Build the entire backend in Python vs Node.js vs a Hybrid model.
* **Decision**: We chose a **Node.js Express server for the main web backend** and a **Python script bridge for the AI query resolver**. 
* **Rationale**: Node.js has robust package installation (`express`, `sqlite3`, `cors`) that succeeded in the sandbox environment, whereas Python's `pip` failed due to connection timeouts. Python, on the other hand, possesses native database parsing libraries (`pdfplumber` and `pypdf` which were already cached/installed) and standard REST libraries for Gemini. Combining them via Node.js spawning Python child processes gives the best of both worlds: a reliable Node.js server to serve resources and mock GraphQL APIs, and a Python engine for data processing and AI query parsing.

### B. SQLite Database Layer
* **Trade-off**: Query files directly (CSV/Excel parsing on the fly) vs using a database.
* **Decision**: We chose to normalize and load the reconstructed CSV files into a **local SQLite database** (`skylark.db`).
* **Rationale**: Querying raw CSV lines via natural language is highly inefficient and complex. Using SQLite allows the Gemini model (or our fallback engine) to write standard SQL queries, enabling rapid aggregations, filtering, joining across tables, and highly accurate results.

### C. Self-contained REST Calls for Gemini
* **Trade-off**: Using Google's `google-genai` SDK vs direct REST API requests.
* **Decision**: We chose **direct HTTP POST requests using Python's standard `urllib.request` library** to call the Gemini API endpoint.
* **Rationale**: Since installing packages failed in pip, relying on external AI SDKs would cause setup errors. The standard HTTP call allows the AI agent to run smoothly without installing any extra libraries.

## 3. What We'd Do Differently With More Time

1. **Monday.com Webhooks**: Set up webhook endpoints to dynamically sync local database records whenever a row is modified or added on monday.com boards, maintaining a real-time analytics cache.
2. **Advanced Charting**: Support more complex charting, such as stacked bar charts for owner sectoral performance or time-series line charts for revenue projection based on tentative close dates.
3. **Natural-Language-to-SQL Guardrails**: Implement SQL sanitization and verification to prevent SQL injection or model hallucination queries (such as checking table/column list white-lists before executing).

## 4. Interpretation of "Leadership Updates"

We interpreted "Leadership Updates" in three ways to provide maximum business utility:
1. **Dynamic Executive Leadership Report**: Built a dedicated workspace inside the Export Reports tab. It queries SQLite in real time, compiling a structured, dynamic summary of pipeline status (Cr value, active deal count, probability-adjusted forecast) and operations deliveries (work order counts, billed amounts, outstanding receivables). Reviewers can copy the text format to the clipboard in one click or download it as a formatted Markdown (`.md`) file.
2. **Interactive Executive Board (Dashboard)**: A dedicated visual dashboard page rendering summary KPIs (total won revenue, active pipeline, total deals, active work orders) and Chart.js graphs mapping sectoral revenue, pipeline health, and top owners sales rankings.
3. **Raw Data Export Cards**: Quick download links to export the fully normalized and merged Deals and Work Orders datasets as CSVs, making them directly importable for offline reports.
4. **Conversational Charting**: Whenever a user asks a question in the chat that aggregates data, the AI agent dynamically attaches a chart configuration to its response, rendering a beautiful visual chart directly inside the chat thread!
