import sqlite3
import csv
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "skylark.db")

def parse_float(val):
    if not val:
        return None
    # Remove whitespace, commas, letters, etc. Keep digits, dots, and minus sign
    val_cleaned = re.sub(r"[^\d\.\-]", "", val)
    if not val_cleaned or val_cleaned == "-":
        return None
    try:
        return float(val_cleaned)
    except ValueError:
        return None

def normalize_date(val):
    if not val:
        return None
    val = val.strip()
    # If YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", val):
        return val
    # If standard date with text or months, e.g. "2025-07-31" or "July" or similar
    # Return as is or standard representation
    return val

def init_db():
    print(f"Initializing database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop tables if they exist
    cursor.execute("DROP TABLE IF EXISTS deals;")
    cursor.execute("DROP TABLE IF EXISTS work_orders;")
    
    # Create deals table
    cursor.execute("""
    CREATE TABLE deals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deal_name TEXT,
        owner_code TEXT,
        client_code TEXT,
        deal_status TEXT,
        close_date_actual TEXT,
        closure_probability TEXT,
        masked_deal_value REAL,
        tentative_close_date TEXT,
        deal_stage TEXT,
        product_deal TEXT,
        sector_service TEXT,
        created_date TEXT
    );
    """)
    
    # Create work_orders table
    cursor.execute("""
    CREATE TABLE work_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deal_name_masked TEXT,
        customer_name_code TEXT,
        serial_num TEXT,
        nature_of_work TEXT,
        last_executed_month TEXT,
        execution_status TEXT,
        data_delivery_date TEXT,
        date_of_po_loi TEXT,
        document_type TEXT,
        probable_start_date TEXT,
        probable_end_date TEXT,
        bd_kam_personnel_code TEXT,
        sector TEXT,
        type_of_work TEXT,
        is_skylark_platform_deliverable TEXT,
        last_invoice_date TEXT,
        latest_invoice_num TEXT,
        amount_excl_gst REAL,
        amount_incl_gst REAL,
        billed_excl_gst REAL,
        billed_incl_gst REAL,
        collected_incl_gst REAL,
        amount_receivable REAL,
        ar_priority_account TEXT,
        quantity_by_ops REAL,
        quantities_as_per_po TEXT,
        quantity_billed_till_date REAL,
        balance_in_quantity REAL,
        invoice_status TEXT,
        expected_billing_month TEXT,
        actual_billing_month TEXT,
        actual_collection_month TEXT,
        wo_status_billed TEXT,
        collection_status TEXT,
        collection_date TEXT,
        billing_status TEXT
    );
    """)
    
    conn.commit()
    conn.close()

def load_data():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Load Deals
    deals_csv = os.path.join(os.path.dirname(__file__), "..", "deals_data.csv")
    if os.path.exists(deals_csv):
        print(f"Loading deals from {deals_csv}...")
        with open(deals_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            deals_rows = []
            for row in reader:
                deals_rows.append((
                    row["Deal Name"],
                    row["Owner code"],
                    row["Client Code"],
                    row["Deal Status"],
                    normalize_date(row["Close Date (A)"]),
                    row["Closure Probability"],
                    parse_float(row["Masked Deal value"]),
                    normalize_date(row["Tentative Close Date"]),
                    row["Deal Stage"],
                    row["Product deal"],
                    row["Sector/service"],
                    normalize_date(row["Created Date"])
                ))
            cursor.executemany("""
            INSERT INTO deals (
                deal_name, owner_code, client_code, deal_status, close_date_actual,
                closure_probability, masked_deal_value, tentative_close_date,
                deal_stage, product_deal, sector_service, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, deals_rows)
            print(f"Loaded {len(deals_rows)} deals.")
            
    # Load Work Orders
    wo_csv = os.path.join(os.path.dirname(__file__), "..", "work_orders_data.csv")
    if os.path.exists(wo_csv):
        print(f"Loading work orders from {wo_csv}...")
        with open(wo_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            wo_rows = []
            for row in reader:
                wo_rows.append((
                    row["Deal name masked"],
                    row["Customer Name Code"],
                    row["Serial #"],
                    row["Nature of Work"],
                    row["Last executed month of recurring project"],
                    row["Execution Status"],
                    normalize_date(row["Data Delivery Date"]),
                    normalize_date(row["Date of PO/LOI"]),
                    row["Document Type"],
                    normalize_date(row["Probable Start Date"]),
                    normalize_date(row["Probable End Date"]),
                    row["BD/KAM Personnel code"],
                    row["Sector"],
                    row["Type of Work"],
                    row["Is any Skylark software platform part of the client deliverables in this deal?"],
                    normalize_date(row["Last invoice date"]),
                    row["latest invoice no."],
                    parse_float(row["Amount in Rupees (Excl of GST) (Masked)"]),
                    parse_float(row["Amount in Rupees (Incl of GST) (Masked)"]),
                    parse_float(row["Billed Value in Rupees (Excl of GST.) (Masked)"]),
                    parse_float(row["Billed Value in Rupees (Incl of GST.) (Masked)"]),
                    parse_float(row["Collected Amount in Rupees (Incl of GST.) (Masked)"]),
                    parse_float(row["Amount Receivable (Masked)"]),
                    row["AR Priority account"],
                    parse_float(row["Quantity by Ops"]),
                    row["Quantities as per PO"],
                    parse_float(row["Quantity billed (till date)"]),
                    parse_float(row["Balance in quantity"]),
                    row["Invoice Status"],
                    row["Expected Billing Month"],
                    row["Actual Billing Month"],
                    row["Actual Collection Month"],
                    row["WO Status (billed)"],
                    row["Collection status"],
                    normalize_date(row["Collection Date"]),
                    row["Billing Status"]
                ))
            cursor.executemany("""
            INSERT INTO work_orders (
                deal_name_masked, customer_name_code, serial_num, nature_of_work,
                last_executed_month, execution_status, data_delivery_date,
                date_of_po_loi, document_type, probable_start_date, probable_end_date,
                bd_kam_personnel_code, sector, type_of_work, is_skylark_platform_deliverable,
                last_invoice_date, latest_invoice_num, amount_excl_gst, amount_incl_gst,
                billed_excl_gst, billed_incl_gst, collected_incl_gst, amount_receivable,
                ar_priority_account, quantity_by_ops, quantities_as_per_po,
                quantity_billed_till_date, balance_in_quantity, invoice_status, expected_billing_month,
                actual_billing_month, actual_collection_month, wo_status_billed, collection_status,
                collection_date, billing_status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
            """, wo_rows)
            print(f"Loaded {len(wo_rows)} work orders.")
            
    conn.commit()
    conn.close()

def query_db(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        # Convert sqlite3.Row items to dictionary
        result = [dict(row) for row in rows]
        conn.close()
        return result
    except Exception as e:
        conn.close()
        raise e

if __name__ == "__main__":
    load_data()
