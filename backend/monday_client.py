import os
import sqlite3
import json
import urllib.request
from backend.database import DB_PATH, query_db

MONDAY_API_URL = "https://api.monday.com/v2"

# Retrieve settings from env
MONDAY_API_KEY = os.environ.get("MONDAY_API_KEY", "")
DEALS_BOARD_ID = os.environ.get("MONDAY_DEALS_BOARD_ID", "")
WO_BOARD_ID = os.environ.get("MONDAY_WO_BOARD_ID", "")

def query_monday_graphql(query, variables=None):
    """Sends a GraphQL request to Monday.com API v2."""
    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json",
        "API-Version": "2023-10"
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
        
    req = urllib.request.Request(
        MONDAY_API_URL, 
        data=json.dumps(payload).encode("utf-8"), 
        headers=headers,
        method="POST"
    )
    
    with urllib.request.urlopen(req) as res:
        response_data = json.loads(res.read().decode("utf-8"))
        if "errors" in response_data:
            raise Exception(f"Monday API Errors: {response_data['errors']}")
        return response_data

def get_real_monday_board(board_id):
    """Queries all items on a real Monday.com board using pagination."""
    query = """
    query ($boardId: [ID!], $cursor: String) {
      boards (ids: $boardId) {
        id
        name
        columns {
          id
          title
          type
        }
        items_page (limit: 500, cursor: $cursor) {
          cursor
          items {
            id
            name
            column_values {
              id
              text
              value
            }
          }
        }
      }
    }
    """
    
    items = []
    cursor = None
    board_name = ""
    columns = []
    
    # Simple pagination loop
    while True:
        variables = {"boardId": [str(board_id)]}
        if cursor:
            variables["cursor"] = cursor
            
        res = query_monday_graphql(query, variables)
        boards = res.get("data", {}).get("boards", [])
        if not boards:
            break
            
        board = boards[0]
        board_name = board.get("name", "")
        columns = board.get("columns", [])
        
        items_page = board.get("items_page", {})
        page_items = items_page.get("items", [])
        items.extend(page_items)
        
        cursor = items_page.get("cursor")
        if not cursor or len(page_items) < 500:
            break
            
    # Flatten items to simple dict list
    flat_rows = []
    for item in items:
        row = {"id": item["id"], "name": item["name"]}
        for val in item.get("column_values", []):
            row[val["id"]] = val["text"]
        flat_rows.append(row)
        
    return flat_rows, board_name, columns

def get_mock_monday_board(board_type):
    """Returns mock board data from our SQLite database formatted like monday.com."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if board_type == "deals":
        cursor.execute("SELECT * FROM deals;")
        rows = [dict(r) for r in cursor.fetchall()]
        board_name = "Deals Board"
        # Map sqlite column names to Monday column specs
        columns = [
            {"id": "deal_name", "title": "Deal Name", "type": "text"},
            {"id": "owner_code", "title": "Owner code", "type": "text"},
            {"id": "client_code", "title": "Client Code", "type": "text"},
            {"id": "deal_status", "title": "Deal Status", "type": "color"},
            {"id": "close_date_actual", "title": "Close Date (A)", "type": "date"},
            {"id": "closure_probability", "title": "Closure Probability", "type": "color"},
            {"id": "masked_deal_value", "title": "Masked Deal value", "type": "numeric"},
            {"id": "tentative_close_date", "title": "Tentative Close Date", "type": "date"},
            {"id": "deal_stage", "title": "Deal Stage", "type": "color"},
            {"id": "product_deal", "title": "Product deal", "type": "text"},
            {"id": "sector_service", "title": "Sector/service", "type": "text"},
            {"id": "created_date", "title": "Created Date", "type": "date"}
        ]
    else: # work_orders
        cursor.execute("SELECT * FROM work_orders;")
        rows = [dict(r) for r in cursor.fetchall()]
        board_name = "Work Orders Board"
        columns = [
            {"id": "deal_name_masked", "title": "Deal name masked", "type": "text"},
            {"id": "customer_name_code", "title": "Customer Name Code", "type": "text"},
            {"id": "serial_num", "title": "Serial #", "type": "text"},
            {"id": "nature_of_work", "title": "Nature of Work", "type": "text"},
            {"id": "last_executed_month", "title": "Last executed month of recurring project", "type": "text"},
            {"id": "execution_status", "title": "Execution Status", "type": "text"},
            {"id": "data_delivery_date", "title": "Data Delivery Date", "type": "date"},
            {"id": "date_of_po_loi", "title": "Date of PO/LOI", "type": "date"},
            {"id": "document_type", "title": "Document Type", "type": "text"},
            {"id": "probable_start_date", "title": "Probable Start Date", "type": "date"},
            {"id": "probable_end_date", "title": "Probable End Date", "type": "date"},
            {"id": "bd_kam_personnel_code", "title": "BD/KAM Personnel code", "type": "text"},
            {"id": "sector", "title": "Sector", "type": "text"},
            {"id": "type_of_work", "title": "Type of Work", "type": "text"},
            {"id": "is_skylark_platform_deliverable", "title": "Is any Skylark software platform part of the client deliverables in this deal?", "type": "text"},
            {"id": "last_invoice_date", "title": "Last invoice date", "type": "date"},
            {"id": "latest_invoice_num", "title": "latest invoice no.", "type": "text"},
            {"id": "amount_excl_gst", "title": "Amount in Rupees (Excl of GST) (Masked)", "type": "numeric"},
            {"id": "amount_incl_gst", "title": "Amount in Rupees (Incl of GST) (Masked)", "type": "numeric"},
            {"id": "billed_excl_gst", "title": "Billed Value in Rupees (Excl of GST.) (Masked)", "type": "numeric"},
            {"id": "billed_incl_gst", "title": "Billed Value in Rupees (Incl of GST.) (Masked)", "type": "numeric"},
            {"id": "collected_incl_gst", "title": "Collected Amount in Rupees (Incl of GST.) (Masked)", "type": "numeric"},
            {"id": "amount_receivable", "title": "Amount Receivable (Masked)", "type": "numeric"},
            {"id": "ar_priority_account", "title": "AR Priority account", "type": "text"},
            {"id": "quantity_by_ops", "title": "Quantity by Ops", "type": "numeric"},
            {"id": "quantities_as_per_po", "title": "Quantities as per PO", "type": "text"},
            {"id": "quantity_billed_till_date", "title": "Quantity billed (till date)", "type": "numeric"},
            {"id": "balance_in_quantity", "title": "Balance in quantity", "type": "numeric"},
            {"id": "invoice_status", "title": "Invoice Status", "type": "text"},
            {"id": "expected_billing_month", "title": "Expected Billing Month", "type": "text"},
            {"id": "actual_billing_month", "title": "Actual Billing Month", "type": "text"},
            {"id": "actual_collection_month", "title": "Actual Collection Month", "type": "text"},
            {"id": "wo_status_billed", "title": "WO Status (billed)", "type": "text"},
            {"id": "collection_status", "title": "Collection status", "type": "text"},
            {"id": "collection_date", "title": "Collection Date", "type": "date"},
            {"id": "billing_status", "title": "Billing Status", "type": "text"}
        ]
    conn.close()
    return rows, board_name, columns

def get_board_records(board_type):
    """Abstraction function to query either the live Monday board or the local database."""
    # Check if we should use the real API or mock
    if MONDAY_API_KEY and MONDAY_API_KEY.lower() != "mock":
        board_id = DEALS_BOARD_ID if board_type == "deals" else WO_BOARD_ID
        if board_id:
            try:
                print(f"Fetching real monday.com board for {board_type} (ID: {board_id})...")
                rows, name, cols = get_real_monday_board(board_id)
                # Map column IDs from Monday to our expected database headers
                # We can align them by title comparison
                title_map = {}
                for col in cols:
                    title_map[col["title"].lower().strip()] = col["id"]
                    
                # Create standard mapped list of dicts
                standard_rows = []
                # Find database column mapping configurations
                _, _, mock_cols = get_mock_monday_board(board_type)
                for r in rows:
                    std_r = {}
                    for m_col in mock_cols:
                        m_title = m_col["title"].lower().strip()
                        m_id = m_col["id"]
                        
                        # Find Monday value using mapped column ID or title
                        monday_col_id = title_map.get(m_title, m_id)
                        val = r.get(monday_col_id, "")
                        std_r[m_id] = val
                    standard_rows.append(std_r)
                return standard_rows
            except Exception as e:
                print(f"Error fetching from live Monday board, falling back to local DB: {e}")
                
    # Fallback to local SQLite database records
    rows, _, _ = get_mock_monday_board(board_type)
    return rows

def handle_mock_graphql(graphql_query):
    """Simulates monday.com API GraphQL responses for local sandbox usage."""
    # Simple check for board queries
    if "boards" in graphql_query:
        # Check if querying Deals or Work Orders
        is_deals = "deals" in graphql_query.lower() or "111" in graphql_query
        board_type = "deals" if is_deals else "work_orders"
        rows, name, columns = get_mock_monday_board(board_type)
        
        # Format response
        items = []
        for idx, r in enumerate(rows):
            column_values = []
            for col in columns:
                col_id = col["id"]
                val = str(r.get(col_id) or "")
                column_values.append({
                    "id": col_id,
                    "text": val,
                    "value": json.dumps({"value": val})
                })
            items.append({
                "id": str(idx + 1000),
                "name": str(r.get("deal_name") or r.get("deal_name_masked") or "Item"),
                "column_values": column_values
            })
            
        return {
            "data": {
                "boards": [
                    {
                        "id": "111" if is_deals else "222",
                        "name": name,
                        "columns": columns,
                        "items_page": {
                            "cursor": None,
                            "items": items
                        }
                    }
                ]
            }
        }
        
    return {"data": {}}
