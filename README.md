# 🚁 Skylark Drones — Monday.com Business Intelligence Agent

> **An AI-powered Business Intelligence Agent built for Skylark Drones to translate natural language into real-time Monday.com metrics.**

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-Streamlit%20Cloud-FF4B4B?style=for-the-badge)](https://skylark-task-tn4qcfwy58rtm6p8vqdckk.streamlit.app/)
[![GitHub](https://img.shields.io/badge/📦%20Source-GitHub-181717?style=for-the-badge)](https://github.com/rohanrathod9740/Skylark-Task)

This BI Agent provides founders and executives with plain-English insights from sales pipelines (Deals Board) and operations records (Work Orders Board), bypassing manual reports or complex database queries.

---

## 🎯 Key Capabilities

- **Dynamic Text-to-SQL Agent**: Parses complex natural language requests, generates SQLite queries, executes them against the cache, and synthesizes answers.
- **Dual-Engine Resolution**: Uses Gemini 2.0 Flash when online; seamlessly falls back to a regex-based SQL template parser when offline.
- **Conversational Memory**: Maintains the last 5 turns of conversation context, resolving pronouns like *"Show Mining deals"* followed by *"What is their value?"*.
- **SQL Safety Guardrail**: A strict whitelist parsing layer blocks non-`SELECT` statements and commands (`DROP`, `DELETE`, etc.) to prevent database exploits.
- **Proactive Executive Insights**: The agent provides confidence levels, flags data quality anomalies (e.g. missing dates, negative receivable offsets), and lists actionable takeaways.
- **Conversational Charting**: Plotly charts (bar, pie, donut) are dynamically generated inside the chat thread to visualize query statistics.
- **Executive Dashboard & Exporter**: Features a dedicated visual analytics dashboard and an automated executive markdown report generator.

---

## 📐 System Architecture

```
                                  ┌──────────────────────────┐
                                  │   Streamlit Cloud / UI   │
                                  └────────────┬─────────────┘
                                               │
                                      [Natural Language]
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │     AI Query Routing Engine      │
                              │ (Gemini 2.0 Flash / Fallback Regex)│
                              └────────────────┬─────────────────┘
                                               │
                                          [Safe SQL]
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │        SQLite Cache Layer        │
                              │      (backend/skylark.db)        │
                              └────────────────┬─────────────────┘
                                               │
                                        [Data Rows]
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │      AI Synthesis Pipeline       │
                              │ (Markdown + Plotly + Metadata JSON)│
                              └──────────────────────────────────┘
```

The application is deployable in two ways:
1. **Streamlit Edition (Production)**: Fully hosted on Streamlit Cloud.
2. **Full-Stack Node.js Edition (Local Developer Sandbox)**: Express server serving a vanilla HTML5/JS dashboard. Queries are resolved via a spawned Python child process.

---

## 📁 Repository Structure

```
Skylark-Task/
├── streamlit_app.py          # streamlt dashboard + chat client + agent logic
├── requirements.txt          # Python dependencies for Streamlit Cloud
├── package.json              # Express server dependencies
│
├── backend/
│   ├── server.js             # Express API server + mock Monday.com GraphQL API
│   ├── agent_resolver.py     # Local Python resolver used by server.js
│   ├── database.py           # SQLite initialization & database seeding
│   ├── monday_client.py      # Monday.com GraphQL API client
│   └── skylark.db            # Local SQLite cache database
│
├── frontend/
│   ├── index.html            # Monday.com-inspired UI (Express version)
│   ├── app.js                # Frontend data rendering and chat (Express version)
│   └── style.css             # Light/Dark mode stylesheets
│
├── reconstruct_data.py       # PDF extraction & alignment script (pdfplumber)
├── deals_data.csv            # Reconstructed Deals dataset
├── work_orders_data.csv      # Reconstructed Work Orders dataset
├── decision_log.md           # Rationale, assumptions, and trade-offs log
└── README.md                 # This file
```

---

## 🛡️ Data Resilience

Raw data was reconstructed from horizontally split PDF pages and normalized to maintain high consistency:

| Issue | Normalization Technique |
|---|---|
| Split Tables Across PDF Pages | Coordinates-based row alignment using `pdfplumber` |
| Financial Values Formatting | Regex extraction to float (handling commas, letters, spaces) |
| Missing/Null Fields | `COALESCE` or `0.0` fallbacks in database inserts and queries |
| Over-billed Work Orders | `CASE WHEN billed > amount THEN 0 ELSE amount - billed END` offset logic |
| Date Formats | Normalization to `YYYY-MM-DD` strings |

---

## 🚀 Live Demo & Setup

### Online Demo
👉 **[Streamlit Live Link](https://skylark-task-tn4qcfwy58rtm6p8vqdckk.streamlit.app/)**

### Local Streamlit Setup
```bash
pip install streamlit pandas plotly pdfplumber
streamlit run streamlit_app.py
```

### Local Express Full-Stack Setup
```bash
# Install node dependencies
npm install

# Initialize database and parse PDFs
npm run reconstruct

# Start Express server
npm start
```
Go to `http://localhost:3000` in your web browser.

---

## 🔑 Recruiter Assessment Deliverables Checklist

- [x] **Hosted Prototype Link**: Deployed at [https://skylark-task-tn4qcfwy58rtm6p8vqdckk.streamlit.app/](https://skylark-task-tn4qcfwy58rtm6p8vqdckk.streamlit.app/)
- [x] **Conversational Chat Interface**: Integrated with dynamic text-to-sql, context memory, and Plotly charting.
- [x] **Monday.com GraphQL Integration**: Real-time board sync. Falls back to SQLite if API keys are mock/absent.
- [x] **Messy Data Normalization Pipeline**: Reconstructed via `reconstruct_data.py` into CSV and SQLite.
- [x] **9 Business Intelligence Queries**: Handled exactly via both AI SQL generation and local fallback regex queries.
- [x] **Executive Update Preparation**: Structured summary report downloadable as `.md`.
- [x] **Decision Log**: Architectural trade-offs, constraints, and decisions documented in `decision_log.md`.
- [x] **Clean Source Code ZIP**: Available on [GitHub remote](https://github.com/rohanrathod9740/Skylark-Task).
