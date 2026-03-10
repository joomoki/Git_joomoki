import sys
import os
from src.stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME

def check_daily_price():
    print("=== Check Daily Price Data ===")
    
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        with db.conn.cursor() as cur:
            # 1. Column names
            cur.execute(f"SELECT * FROM {SCHEMA_NAME}.daily_price LIMIT 1")
            col_names = [desc[0] for desc in cur.description]
            print(f"Columns: {col_names}")
            
            row = cur.fetchone()
            print(f"Sample Row: {row}")
            
            if row:
                print("\nColumn-Value Mapping:")
                for col, val in zip(col_names, row):
                    print(f"  {col}: {val}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    check_daily_price()
