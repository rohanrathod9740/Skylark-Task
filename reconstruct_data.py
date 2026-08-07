import pdfplumber
import csv
import os

brain_dir = r"C:\Users\ratho\.gemini\antigravity-ide\brain\c64f04e7-af36-4faa-82f9-af99846258ec"
pdf1_path = os.path.join(brain_dir, "media__1786087595640.pdf") # Deals
pdf2_path = os.path.join(brain_dir, "media__1786087595661.pdf") # Work Orders

# Deals columns config
pdf1_config = [
    # Set 1 (Pages 1-9): Columns 1-6
    {
        "cols": [
            ("Deal Name", 0, 115),
            ("Owner code", 115, 185),
            ("Client Code", 185, 270),
            ("Deal Status", 270, 350),
            ("Close Date (A)", 350, 435),
            ("Closure Probability", 435, 600)
        ]
    },
    # Set 2 (Pages 10-18): Columns 7-10
    {
        "cols": [
            ("Masked Deal value", 0, 145),
            ("Tentative Close Date", 145, 225),
            ("Deal Stage", 225, 385),
            ("Product deal", 385, 600)
        ]
    },
    # Set 3 (Pages 19-27): Columns 11-12
    {
        "cols": [
            ("Sector/service", 0, 160),
            ("Created Date", 160, 600)
        ]
    }
]

# Work Orders columns config
pdf2_config = [
    # Set 1 (Pages 1-5): Cols 0-3
    {"cols": [("Deal name masked", 0, 195), ("Customer Name Code", 195, 310), ("Serial #", 310, 420), ("Nature of Work", 420, 600)]},
    # Set 2 (Pages 6-10): Cols 4-6
    {"cols": [("Last executed month of recurring project", 0, 240), ("Execution Status", 240, 360), ("Data Delivery Date", 360, 600)]},
    # Set 3 (Pages 11-15): Cols 7-10
    {"cols": [("Date of PO/LOI", 0, 150), ("Document Type", 150, 255), ("Probable Start Date", 255, 365), ("Probable End Date", 365, 600)]},
    # Set 4 (Pages 16-20): Cols 11-12
    {"cols": [("BD/KAM Personnel code", 0, 230), ("Sector", 230, 600)]},
    # Set 5 (Pages 21-25): Cols 13-14
    {"cols": [("Type of Work", 0, 240), ("Is any Skylark software platform part of the client deliverables in this deal?", 240, 600)]},
    # Set 6 (Pages 26-30): Cols 15-17
    {"cols": [("Last invoice date", 0, 150), ("latest invoice no.", 150, 260), ("Amount in Rupees (Excl of GST) (Masked)", 260, 600)]},
    # Set 7 (Pages 31-35): Col 18
    {"cols": [("Amount in Rupees (Incl of GST) (Masked)", 0, 600)]},
    # Set 8 (Pages 36-40): Col 19
    {"cols": [("Billed Value in Rupees (Excl of GST.) (Masked)", 0, 600)]},
    # Set 9 (Pages 41-45): Cols 20-21
    {"cols": [("Billed Value in Rupees (Incl of GST.) (Masked)", 0, 290), ("Collected Amount in Rupees (Incl of GST.) (Masked)", 290, 600)]},
    # Set 10 (Pages 46-50): Cols 22-23
    {"cols": [("Amount to be billed in Rs. (Exl. of GST) (Masked)", 0, 270), ("Amount to be billed in Rs. (Incl. of GST) (Masked)", 270, 600)]},
    # Set 11 (Pages 51-55): Cols 24-27
    {"cols": [("Amount Receivable (Masked)", 0, 200), ("AR Priority account", 200, 315), ("Quantity by Ops", 315, 415), ("Quantities as per PO", 415, 600)]},
    # Set 12 (Pages 56-60): Cols 28-31
    {"cols": [("Quantity billed (till date)", 0, 160), ("Balance in quantity", 160, 265), ("Invoice Status", 265, 355), ("Expected Billing Month", 355, 600)]},
    # Set 13 (Pages 61-65): Cols 32-35
    {"cols": [("Actual Billing Month", 0, 150), ("Actual Collection Month", 150, 265), ("WO Status (billed)", 265, 365), ("Collection status", 365, 600)]},
    # Set 14 (Pages 66-70): Cols 36-37
    {"cols": [("Collection Date", 0, 150), ("Billing Status", 150, 600)]}
]

def clean_row_value(val):
    if val is None:
        return ""
    val_clean = val.strip().replace("\n", " ")
    # Replace multiple spaces with a single space
    while "  " in val_clean:
        val_clean = val_clean.replace("  ", " ")
    return val_clean

def is_header_line(line_text):
    header_keywords = [
        "Deal Name", "Owner code", "Client Code", "Deal Status", "Close Date", "Closure Probability",
        "Masked Deal", "Tentative Close", "Deal Stage", "Product deal", "Sector/service", "Created Date",
        "Deal name masked", "Customer Name", "Serial #", "Nature of Work", "Last executed", "recurring project",
        "Execution Status", "Data Delivery", "Date of PO", "Document Type", "Probable Start", "Probable End",
        "BD/KAM Personnel", "Sector", "Type of Work", "Skylark software", "client deliverables",
        "Last invoice date", "latest invoice", "Amount in Rupees", "GST) (Masked", "Billed Value", "Collected Amount",
        "Amount to be billed", "Rs. (Exl. of GST", "Rs. (Incl. of GST", "Amount Receivable", "AR Priority",
        "Quantity by Ops", "Quantities as per PO", "Quantity billed", "Balance in quantity", "Invoice Status",
        "Expected Billing", "Actual Billing", "Actual Collection", "WO Status (billed)", "Collection status",
        "Collection Date", "Billing Status"
    ]
    for kw in header_keywords:
        if kw.lower() in line_text.lower():
            return True
    return False

def parse_pdf(pdf_path, config_list, pages_per_set):
    print(f"Parsing {os.path.basename(pdf_path)}...")
    rows_per_page = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages):
            set_idx = idx // pages_per_set
            config = config_list[set_idx]
            cols = config["cols"]
            
            words = page.extract_words()
            if not words:
                rows_per_page[idx] = []
                continue
                
            # Group words by approximate top coordinate
            lines = {}
            for w in words:
                matched_top = None
                for t in lines.keys():
                    if abs(t - w['top']) < 3:
                        matched_top = t
                        break
                if matched_top is None:
                    lines[w['top']] = [w]
                else:
                    lines[matched_top].append(w)
            
            # Sort lines by top position
            sorted_tops = sorted(lines.keys())
            
            page_rows = []
            for top in sorted_tops:
                line_words = sorted(lines[top], key=lambda w: w['x0'])
                line_text = " ".join(w['text'] for w in line_words)
                
                if is_header_line(line_text):
                    continue # Skip header row
                
                # Align words to columns
                row_data = {col_name: [] for col_name, _, _ in cols}
                for w in line_words:
                    center_x = (w['x0'] + w['x1']) / 2.0
                    assigned = False
                    for col_name, x_min, x_max in cols:
                        if x_min <= center_x < x_max:
                            row_data[col_name].append(w['text'])
                            assigned = True
                            break
                    if not assigned:
                        # Assign to closest column
                        min_dist = 9999
                        closest_col = None
                        for col_name, x_min, x_max in cols:
                            dist = min(abs(center_x - x_min), abs(center_x - x_max))
                            if dist < min_dist:
                                min_dist = dist
                                closest_col = col_name
                        if closest_col:
                            row_data[closest_col].append(w['text'])
                
                # Join word snippets in each column
                row_dict = {}
                for col_name in row_data:
                    row_dict[col_name] = clean_row_value(" ".join(row_data[col_name]))
                
                # Check if row is completely empty
                if any(row_dict.values()):
                    page_rows.append(row_dict)
            
            rows_per_page[idx] = page_rows
            print(f"Page {idx+1} parsed: found {len(page_rows)} data rows")
            
    return rows_per_page

def reconstruct_deals():
    # 27 pages, 3 sets, 9 pages per set
    rows_per_page = parse_pdf(pdf1_path, pdf1_config, 9)
    all_deals = []
    
    # Define headers in order
    headers = [
        "Deal Name", "Owner code", "Client Code", "Deal Status", "Close Date (A)", "Closure Probability",
        "Masked Deal value", "Tentative Close Date", "Deal Stage", "Product deal",
        "Sector/service", "Created Date"
    ]
    
    for page_in_set in range(9):
        p0 = page_in_set
        p1 = page_in_set + 9
        p2 = page_in_set + 18
        
        len0 = len(rows_per_page[p0])
        len1 = len(rows_per_page[p1])
        len2 = len(rows_per_page[p2])
        
        max_len = max(len0, len1, len2)
        print(f"Aligning Deals Set Page {page_in_set+1}: row counts {len0}, {len1}, {len2} -> using max {max_len}")
        
        for r_idx in range(max_len):
            row_dict = {}
            for h in headers:
                row_dict[h] = ""
            
            if r_idx < len0:
                row_dict.update(rows_per_page[p0][r_idx])
            if r_idx < len1:
                row_dict.update(rows_per_page[p1][r_idx])
            if r_idx < len2:
                row_dict.update(rows_per_page[p2][r_idx])
                
            all_deals.append(row_dict)
            
    # Write to CSV
    output_path = "deals_data.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_deals)
    print(f"Successfully reconstructed Deals: wrote {len(all_deals)} rows to {output_path}")

def reconstruct_work_orders():
    # 70 pages, 14 sets, 5 pages per set
    rows_per_page = parse_pdf(pdf2_path, pdf2_config, 5)
    all_wos = []
    
    # Define headers in order
    headers = [
        "Deal name masked", "Customer Name Code", "Serial #", "Nature of Work",
        "Last executed month of recurring project", "Execution Status", "Data Delivery Date",
        "Date of PO/LOI", "Document Type", "Probable Start Date", "Probable End Date",
        "BD/KAM Personnel code", "Sector",
        "Type of Work", "Is any Skylark software platform part of the client deliverables in this deal?",
        "Last invoice date", "latest invoice no.", "Amount in Rupees (Excl of GST) (Masked)",
        "Amount in Rupees (Incl of GST) (Masked)",
        "Billed Value in Rupees (Excl of GST.) (Masked)",
        "Billed Value in Rupees (Incl of GST.) (Masked)", "Collected Amount in Rupees (Incl of GST.) (Masked)",
        "Amount to be billed in Rs. (Exl. of GST) (Masked)", "Amount to be billed in Rs. (Incl. of GST) (Masked)",
        "Amount Receivable (Masked)",
        "AR Priority account", "Quantity by Ops", "Quantities as per PO",
        "Quantity billed (till date)", "Balance in quantity", "Invoice Status", "Expected Billing Month",
        "Actual Billing Month", "Actual Collection Month", "WO Status (billed)", "Collection status",
        "Collection Date", "Billing Status"
    ]
    
    for page_in_set in range(5):
        len_list = [len(rows_per_page[page_in_set + s * 5]) for s in range(14)]
        max_len = max(len_list)
        print(f"Aligning Work Orders Set Page {page_in_set+1}: row counts {len_list} -> using max {max_len}")
        
        for r_idx in range(max_len):
            row_dict = {}
            for h in headers:
                row_dict[h] = ""
                
            for s in range(14):
                p_idx = page_in_set + s * 5
                if r_idx < len(rows_per_page[p_idx]):
                    row_dict.update(rows_per_page[p_idx][r_idx])
            all_wos.append(row_dict)
            
    # Write to CSV
    output_path = "work_orders_data.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_wos)
    print(f"Successfully reconstructed Work Orders: wrote {len(all_wos)} rows to {output_path}")

if __name__ == "__main__":
    reconstruct_deals()
    reconstruct_work_orders()
