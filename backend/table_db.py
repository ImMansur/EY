# table_db.py
"""
Database utilities for the Query Management Agent.
Handles reading from and writing to QMT Data New.xlsx (multi-sheet Excel file).
"""

import pandas as pd
import os
from datetime import datetime

FILE = "QMT Data New.xlsx"


def get_all_tickets_df(sheet_name="Tickets"):
    """
    Load the Tickets sheet into a DataFrame.
    Properly handles Excel serial dates → datetime conversion only when needed.
    """
    if not os.path.exists(FILE):
        # Check parent dir if not found (optional, but keep it simple for now as it's in the same folder)
        raise FileNotFoundError(f"{FILE} not found. Please place the file in the working directory.")

    try:
        df = pd.read_excel(FILE, sheet_name=sheet_name, engine="openpyxl")
        
        # Ensure key columns are string type for reliable matching
        for col in ["Ticket ID", "User ID", "User Name", "Assigned Team", "Ticket Type"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Handle Excel serial dates → datetime only if column is still numeric
        date_cols = ["Creation Date", "Ticket Closed Date", "Ticket Updated Date"]
        origin = pd.Timestamp("1899-12-30")
        
        for col in date_cols:
            if col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    # Raw Excel serial numbers → apply origin correction
                    df[col] = origin + pd.to_timedelta(df[col], unit='D')
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    # Already parsed as datetime by read_excel → keep as is
                    pass
                else:
                    # Fallback: try to convert (strings, mixed types, etc.)
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    except Exception as e:
        raise RuntimeError(f"Failed to load sheet '{sheet_name}': {str(e)}")


def get_invoices_df():
    """
    Load the Invoice sheet into a DataFrame.
    Properly handles Excel serial dates → datetime conversion only when needed.
    """
    if not os.path.exists(FILE):
        raise FileNotFoundError(f"{FILE} not found.")
    
    try:
        df = pd.read_excel(FILE, sheet_name="Invoice", engine="openpyxl")
        
        if "Invoice Number" in df.columns:
            df["Invoice Number"] = df["Invoice Number"].astype(str).str.strip()
            
        # Handle date columns
        date_cols = ["Invoice Date", "Due Date", "Clearing Date", "Posting Date", "Document Date"]
        origin = pd.Timestamp("1899-12-30")
        
        for col in date_cols:
            if col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = origin + pd.to_timedelta(df[col], unit='D')
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    pass
                else:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    except Exception as e:
        raise RuntimeError(f"Failed to load Invoice sheet: {str(e)}")


def save_tickets_df(df, sheet_name="Tickets"):
    """
    Save the DataFrame back to the specified sheet in the Excel file.
    Overwrites the sheet if it exists.
    """
    try:
        with pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"Saved changes to sheet '{sheet_name}' successfully.")
    except Exception as e:
        print(f"Failed to save DataFrame: {str(e)}")


def ensure_required_columns(df):
    """
    Add missing utility columns if they don't exist.
    """
    if "Ticket Updated Date" not in df.columns:
        df["Ticket Updated Date"] = pd.NA
    if "Auto Resolved" not in df.columns:
        df["Auto Resolved"] = False
    return df


def update_ticket(ticket_id: str, field: str, value: any) -> bool:
    """
    Update a specific field for a given ticket ID.
    """
    try:
        df = get_all_tickets_df()
        df = ensure_required_columns(df)

        search_id = str(ticket_id).strip()

        field_map = {
            "Team Name":        "Assigned Team",
            "Person Name":      "User Name",
            "Person ID":        "User ID",
            "Ticket Create Date": "Creation Date",
            "Ticket Closed Date": "Ticket Closed Date",
            "Ticket Updated Date": "Ticket Updated Date",
            "Ticket Status":    "Ticket Status",
            "Ticket Priority":  "Priority",
        }
        real_field = field_map.get(field, field)

        if real_field not in df.columns:
            print(f"Field '{real_field}' not found.")
            return False

        mask = df["Ticket ID"] == search_id
        if not mask.any():
            print(f"Ticket {ticket_id} not found.")
            return False

        # Normalize value
        if real_field == "Assigned Team":
            value = str(value).strip().upper() if value is not None else None
        elif real_field == "User Name":
            value = str(value).strip().title() if value is not None else None
        elif real_field in ["User ID", "Ticket ID"]:
            value = str(value) if value is not None else None
        elif real_field in ["Creation Date", "Ticket Closed Date", "Ticket Updated Date"]:
            try:
                value = pd.to_datetime(value, errors='coerce')
            except:
                value = str(value) if value is not None else None

        df.loc[mask, real_field] = value

        # Update timestamp
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.loc[mask, "Ticket Updated Date"] = now_str

        save_tickets_df(df)
        return True

    except Exception as e:
        print(f"Update failed: {str(e)}")
        return False


def add_auto_resolved_flag(ticket_id: str, is_auto: bool = True) -> bool:
    return update_ticket(ticket_id, "Auto Resolved", is_auto)


if __name__ == "__main__":
    try:
        df_t = get_all_tickets_df()
        df_i = get_invoices_df()
        print("Tickets loaded:", df_t.shape)
        print("Invoices loaded:", df_i.shape)
        
        print("\nCreation Date sample (should be datetime):")
        print(df_t["Creation Date"].head(10))
        
        print("\nDue Date sample (should be datetime):")
        print(df_i["Due Date"].head(10))
    except Exception as e:
        print("Error:", str(e))
