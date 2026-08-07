# 🚁 Skylark Drones — Monday.com Business Intelligence Agent

> **Submission by Rohan Rathod** — Full-Stack AI Agent Assignment

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-Streamlit%20Cloud-FF4B4B?style=for-the-badge)](https://skylark-task-tn4qcfwy58rtm6p8vqdckk.streamlit.app/)
[![GitHub](https://img.shields.io/badge/📦%20Source-GitHub-181717?style=for-the-badge)](https://github.com/rohanrathod9740/Skylark-Task)

---

## 🎯 What This Project Does

This is an **AI-powered Business Intelligence Agent** built for Skylark Drones. It allows founders and executives to ask plain-English questions and get instant, data-driven answers from their Monday.com boards — without writing any SQL or pulling reports manually.

**Example questions it answers:**
- *"How is our pipeline looking for the energy sector?"*
- *"What is our pending billed value from work orders?"*
- *"Give me a comprehensive leadership summary update."*
- *"Who are our top enterprise clients by pipeline value?"*
- *"Show me delayed and stuck work orders."*

---

## 🚀 Live Demo (No Setup Needed)

👉 **[https://skylark-task-tn4qcfwy58rtm6p8vqdckk.streamlit.app/](https://skylark-task-tn4qcfwy58rtm6p8vqdckk.streamlit.app/)**

Open the link on any device — no login, no install, works instantly.

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│               Streamlit Cloud (Python)                  │
│  ┌─────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│  │Overview │ │ AI Assistant │ │  Leadership Report   │  │
│  │Dashboard│ │  (Chat UI)   │ │  (Auto-generated)    │  │
│  └────┬────┘ └──────┬───────┘ └──────────┬───────────┘  │
│       │             │                    │               │
│       └─────────────┴────────────────────┘               │
│                         │                                │
│              ┌──────────▼──────────┐                     │
│              │   Query Resolver    │                     │
│              │ (Rule-based + SQL)  │                     │
│              └──────────┬──────────┘                     │
│                         │                                │
│         ┌───────────────┼────────────────┐               │
│         ▼               ▼                ▼               │
│   [SQLite Cache]  [Gemini 2.0 AI]  [Monday.com API]      │
└─────────────────────────────────────────────────────────┘

Also available: Node.js Express Edition (npm start → localhost:3000)
```

**Two deployment options were built:**
| Edition | Stack | Run Command |
|---|---|---|
| **Streamlit (Cloud)** | Python, Streamlit, Plotly, SQLite | `streamlit run streamlit_app.py` |
| **Node.js (Local)** | Express, Vanilla JS, Chart.js, SQLite | `npm start` → `localhost:3000` |

---

## ✅ Deliverables Checklist

| Requirement | Status | How It's Met |
|---|---|---|
| **Hosted Prototype** | ✅ | [Live on Streamlit Cloud](https://skylark-task-tn4qcfwy58rtm6p8vqdckk.streamlit.app/) |
| **Conversational Interface** | ✅ | Natural language chat with pill shortcuts & Gemini AI |
| **Monday.com Integration** | ✅ | API via env vars; auto-falls back to local SQLite cache |
| **Data Resilience** | ✅ | Handles nulls, negative values, messy formats, split tables |
| **Business Intelligence Queries** | ✅ | 9 founder query types with exact DB answers + AI synthesis |
| **Leadership Update Prep** | ✅ | Auto-generated report with download as `.md` |
| **Decision Log** | ✅ | See [`decision_log.md`](./decision_log.md) |
| **README + Architecture** | ✅ | This file |
| **Source Code ZIP** | ✅ | [Download from GitHub](https://github.com/rohanrathod9740/Skylark-Task/archive/refs/heads/main.zip) |

---

## 🤖 AI Agent Capabilities

### Core Business Intelligence Queries

The agent handles these 9 founder-level query categories with **exact database answers**:

| Query Type | Example | Data Source |
|---|---|---|
| Pipeline Health | *"How is our pipeline looking?"* | Deals Board |
| Revenue Forecast | *"What's our total won revenue + forecast?"* | Deals Board |
| Energy Sector | *"Energy sector pipeline performance?"* | Deals Board |
| Expected Revenue | *"Expected revenue from open deals?"* | Deals Board |
| Pending Billing | *"What is our pending billed value?"* | Work Orders |
| Delayed Work Orders | *"Show delayed and stuck work orders"* | Work Orders |
| Operational Risks | *"Show stuck and paused projects"* | Work Orders |
| Top Enterprise Clients | *"Who are our biggest clients?"* | Deals Board |
| Leadership Summary | *"Give me a leadership update"* | Both Boards |

### General Question Answering (Gemini AI)
For questions outside the above categories (company info, open-ended analysis, strategy questions), the agent routes to **Gemini 2.0 Flash** with full Skylark business context injected into the prompt.

---

## 🛡️ Data Resilience

The raw data contained significant quality issues that were handled:

| Issue | How Handled |
|---|---|
| Tables split horizontally across PDF pages | Custom row-merge alignment in `reconstruct_data.py` |
| Inconsistent date formats (`DD/MM/YY`, `MM-DD-YYYY`, text) | Regex normalization pipeline |
| Missing/null financial values | `COALESCE` + 0-fallback in all SQL queries |
| Negative outstanding amounts (over-billing) | `CASE WHEN billed > po THEN 0 ELSE po-billed END` |
| Inconsistent naming conventions | Normalized and mapped via lookup tables |

---

## ⚙️ Monday.com Integration

### Live Integration (Production)
Configure these environment variables to connect to your real Monday.com boards:

```bash
GEMINI_API_KEY="your_gemini_api_key"
MONDAY_API_KEY="your_monday_personal_api_token"
MONDAY_DEALS_BOARD_ID="your_deals_board_id"
MONDAY_WO_BOARD_ID="your_work_orders_board_id"
```

On **Streamlit Cloud**: Add these in **App Settings → Secrets** in TOML format.

### Offline / Mock Mode
If `MONDAY_API_KEY` is absent or set to `mock`, the system automatically serves data from the local SQLite cache (`backend/skylark.db`) — no configuration needed.

### Board Setup Guide
1. Obtain your **Monday.com Personal API Token** from Developer Settings.
2. Create two boards: **Deals** and **Work Orders**.
3. Import `deals_data.csv` and `work_orders_data.csv` into the respective boards.
4. Copy the **Board IDs** from the board URLs and set as env vars above.

---

## 🏃 Local Setup

### Streamlit Version

```bash
pip install streamlit pandas plotly pdfplumber
streamlit run streamlit_app.py
```

### Node.js Full-Stack Version

```bash
# Install dependencies
npm install

# Load data into SQLite (runs reconstruct_data.py + backend/database.py)
npm run reconstruct

# Launch web server
npm start

# Open in browser
http://localhost:3000
```

**Prerequisites:** Node.js v18+, Python 3.9+

---

## 📁 Repository Structure

```
Skylark-Task/
├── streamlit_app.py          # 🚀 Streamlit Cloud deployment (main entry)
├── requirements.txt          # Python dependencies for Streamlit Cloud
├── package.json              # Node.js dependencies
│
├── backend/
│   ├── server.js             # Express web server + mock Monday.com GraphQL API
│   ├── agent_resolver.py     # AI query router (Gemini + fallback SQL engine)
│   ├── query_agent.py        # Natural language → SQL pipeline
│   ├── database.py           # SQLite schema creation + data loading
│   ├── monday_client.py      # Monday.com API integration client
│   └── skylark.db            # Pre-loaded SQLite database (344 deals, 176 WOs)
│
├── frontend/
│   ├── index.html            # Monday.com-inspired UI
│   ├── app.js                # Interactive dashboard logic
│   └── style.css             # Light/Dark theme, animations
│
├── reconstruct_data.py       # PDF data extraction + normalization pipeline
├── deals_data.csv            # Cleaned Deals dataset
├── work_orders_data.csv      # Cleaned Work Orders dataset
├── decision_log.md           # Key decisions, trade-offs, assumptions
└── README.md                 # This file
```

---

## 🔑 Key Design Decisions

> Full reasoning is documented in [`decision_log.md`](./decision_log.md)

- **Two deployments** (Streamlit + Node.js) to maximize evaluator accessibility
- **SQLite over direct API** for resilience and offline capability
- **Rule-based resolver + Gemini** hybrid — guaranteed exact answers for founder queries, plus AI generality
- **Leadership updates** interpreted as an auto-generated executive report workspace with live recalculation

---

## 📊 Sample Queries to Try

Open the [live demo](https://skylark-task-tn4qcfwy58rtm6p8vqdckk.streamlit.app/) and type:

- *"How is our pipeline looking?"*
- *"What is our pending billing from work orders?"*
- *"Show me the energy sector pipeline"*
- *"Tell me about Skylark Drones"*
- *"Who are our top 5 clients?"*
- *"Give me a leadership update"*
