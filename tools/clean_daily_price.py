import sys
import os
from src.stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME

def clean_daily_price():
    print("=== Clean Daily Price Data (Feb 19) ===")
    
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        with db.conn.cursor() as cur:
            # Check count before delete
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.daily_price WHERE trade_date = '2026-02-19'")
            count = cur.fetchone()[0]
            print(f"Rows to delete: {count}")
            
            if count > 0:
                cur.execute(f"DELETE FROM {SCHEMA_NAME}.daily_price WHERE trade_date = '2026-02-19'")
                db.conn.commit()
                print("Deleted successfully.")
            else:
                print("No rows to delete.")

    except Exception as e:
        print(f"Error: {e}")
        db.conn.rollback()
    finally:
        db.disconnect()

if __name__ == "__main__":
    clean_daily_price()
