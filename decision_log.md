# 📝 Skylark Drones BI Agent — Engineering Decision Log

> **This log documents the assumptions, priorities, trade-offs, and critical technical choices made during the development of the Skylark Drones BI Agent.**

---

## 1. Assumptions & Data Constraints

### A. Coordinate-Based PDF Row Extraction
*   **Assumption**: The PDF datasets represent horizontal grid splits across pages where row indexes align vertically (Row 1 on Page 1 corresponds to Row 1 on Page 10).
*   **Engineering Decision**: Column headers were matched using spatial bounding boxes in `reconstruct_data.py`. Alignment checks enforce indexing matches before stitching columns to prevent dataset shifts.

### B. Currency & Financial Arithmetic
*   **Assumption**: Values are denominated in Indian Rupees (INR) and are represented as standard floats.
*   **Engineering Decision**: Standardized conversions divide raw database floats to print values in Crore (₹ Cr) or Lakhs (₹ L) dynamically. Commas and currency symbols are cleaned during ingestion.

### C. Over-Billing Adjustment
*   **Assumption**: When billed amounts exceed purchase order values (billed > PO), it indicates billing adjustments or source data anomalies.
*   **Engineering Decision**: Applied a floor filter: `CASE WHEN billed_excl_gst > amount_excl_gst THEN 0 ELSE amount_excl_gst - billed_excl_gst END` when calculating pending collections, preventing negative balances from distorting aggregate BI forecasts.

---

## 2. Priority Strategy (MoSCoW framework)

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│              MUST HAVE                │              SHOULD HAVE              │
│  - Coordinate PDF reconstruction      │  - Conversational memory (5 turns)     │
│  - SQLite database caching layer      │  - Markdown executive .md exporter    │
│  - SQL Safety validator rules         │  - Interactive Plotly chart builders   │
├───────────────────────────────────────┼───────────────────────────────────────┤
│              COULD HAVE               │              WON'T HAVE               │
│  - Client-side 3D orbital canvas      │  - Multi-tenant credential logins     │
│  - Ambient background glow effects    │  - Writing back to monday.com boards  │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

---

## 3. Architecture Trade-offs & Decisions

### A. Caching Database (SQLite) vs. Direct Real-Time GraphQL Queries
*   **Context**: GraphQL connects directly to Monday.com, but query processing is limited by rate caps and network latencies.
*   **Decision**: Cache board records into a local SQLite database (`backend/skylark.db`), updating it on query intervals.
*   **Trade-off**: Caching introduces a data fresh delay (cache sync is run on request). This is accepted because sales pipelines and work orders do not require sub-second live consistency for executive planning.

### B. SQLite Relational Engine vs. In-Memory Pandas Dataframes
*   **Context**: Pandas can filter data in memory, but joining nested columns becomes complex.
*   **Decision**: Seed SQLite and execute raw SQL statements via SQLite client library.
*   **Trade-off**: SQL commands require a database management wrapper but provide clean syntax, low memory usage, and robust execution.

---

## 4. Prioritized Business Value

"Leadership Updates" are interpreted in four layers to provide immediate executive value:
1. **Dynamic Summaries**: Consolidates revenue, pipelines, and project delivery metrics.
2. **Visual Dashboard**: Renders group status configurations dynamically using Plotly charts.
3. **Proactive Advice**: Appends data warnings (e.g. over-billing warnings) and recommendations directly inside assistant replies.
4. **Markdown Export**: Formats summaries to copy or download directly as `.md` reports.
