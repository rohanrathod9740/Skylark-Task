# Skylark Business Intelligence (BI) Agent

An AI-powered conversational agent and executive dashboard integrated with Monday.com boards (Deals and Work Orders). It handles messy data, standardizes formats, and provides founder-level insights.

## Project Architecture

```
+--------------------------------------------------------+
|                      Frontend UI                       |
|           (HTML5, Vanilla CSS, App.js, Chart.js)        |
+---------------------------+----------------------------+
                            |
                            | (HTTP Requests)
                            v
+--------------------------------------------------------+
|                Node.js Express Backend                 |
|                   (server.js, SQLite)                  |
+-------------+-------------+--------------+-------------+
              |             |              |
              |             |              | (Spawn Script)
              |             |              v
              |             |    +-----------------------+
              |             |    |    query_agent.py     |
              |             |    +-----------+-----------+
              |             |                |
              |             |                v
              |             |    +-----------------------+
              |             |    |   agent_resolver.py   |
              |             |    | (Gemini SQL / Fallback|
              |             |    |     Query Engine)     |
              |             |    +-----------+-----------+
              |             |                |
              v             v                v
       [skylark.db]   [mock graphql]  [Google Gemini API]
```

* **Frontend**: Responsive Light/Dark theme mirroring the monday.com brand, featuring a conversational chatbot, an Executive Board with visual graphs (Chart.js), a Data Explorer with raw spreadsheet grids, and a split-pane reports workspace.
* **Backend**: Node.js Express server acting as a unified web asset host, data exporter, and a mock Monday.com v2 GraphQL API provider.
* **Database**: Local SQLite database storing clean, normalized Deals and Work Orders datasets parsed from messy multi-page PDFs.
* **AI Query Engine**: Python-based agent resolver translating natural language queries to SQLite SQL via Gemini 2.5 Flash, returning data along with synthesized business insights and visual charts.

---

## Key Features

1. **Executive Leadership Update Workspace**: A dedicated split-pane dashboard that aggregates sales pipeline values (Crore), probability-adjusted forecast numbers, and completed operational deliveries (Lakhs) in real time. Features single-click clipboard copying and document download in Markdown (`.md`) format.
2. **AI Conversational Assistant with Charting**: Instantly answers complex text questions. Outputs the executed SQL query and automatically appends relevant visual charts (Bar, Pie, Doughnut) inside the chat feed.
3. **Permanent Suggested Founder Queries**: A panel of quick-pill capsules for the 9 core founder business queries (Revenue Forecast, Energy Performance, Operational Risks, Pending Billing, etc.), mapped to strict fallback calculations.
4. **Data Explorer Grid**: An interactive spreadsheet table viewer displaying all reconstructed Deals and Work Orders with live keyword searching, multi-status filters, and CSV view exports.
5. **Light & Dark Theme Switcher**: Full-app theme toggle caching choices in LocalStorage and dynamically recalculating Chart.js gridlines/scales on theme updates.

---

## Error Handling & Data Resilience

* **Data Normalization & Cleaning**: Gracefully standardizes chaotic date formats, aligns horizontal multi-page split records, maps client/owner IDs, and adjusts for negative outstanding PO balances.
* **Gemini API Fallback Resolver**: If the Gemini API key is missing or encounters HTTP Rate Limit errors (HTTP 429), queries are instantly intercepted by a keyword routing system that computes exact figures from the database.
* **Out-of-the-Box Mock Mode**: If live Monday.com integration variables are not defined, the system automatically falls back to execute mock API endpoints using the local SQLite cache.

---

## Getting Started

### Prerequisites
* **Node.js** (v18+)
* **Python** (v3+)

### Installation & Initialization

1. Clone or copy the project files to your workspace directory.
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. Run the data reconstruction script to extract the split tables from the PDFs, normalize values, and load them into the local SQLite database:
   ```bash
   npm run reconstruct
   ```
   *This command will execute `reconstruct_data.py` followed by `backend/database.py`.*

4. Launch the full-stack web server:
   ```bash
   npm start
   ```
5. Open your browser and navigate to `http://localhost:3000`.

---

## Configuration & Monday.com Integration

To connect the agent to your live Monday.com boards instead of the mock local database:

1. Obtain your **Monday.com Developer Personal API Token** from your Monday.com developer profile.
2. Create two Monday.com boards:
   * **Deals**: Import the reconstructed `deals_data.csv` file.
   * **Work Orders**: Import the reconstructed `work_orders_data.csv` file.
3. Retrieve the **Board IDs** from the Monday.com board URLs.
4. Set the following environment variables on your server configuration:
   ```bash
   PORT=3000
   MONDAY_API_KEY="your_actual_monday_token_here"
   MONDAY_DEALS_BOARD_ID="your_deals_board_id"
   MONDAY_WO_BOARD_ID="your_work_orders_board_id"
   GEMINI_API_KEY="your_gemini_api_key_here"
   ```
   *(If `MONDAY_API_KEY` is empty, missing, or set to `"mock"`, the system automatically falls back to serve local database mock endpoints).*

---

## Sample Conversational Queries to Try
* *"How is our pipeline looking?"*
* *"Show sectoral performance"*
* *"Which owner has the highest billed value?"*
* *"What is our total revenue from Renewables?"*
* *"Give me a summary of work orders execution"*
