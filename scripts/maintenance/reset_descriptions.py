import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager, SCHEMA_NAME

def reset_descriptions():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection failed")
        return

    try:
        with db.conn.cursor() as cur:
            # Set description to NULL for all KR stocks
            # assuming KR stocks are in stock_companies table
            sql = f"UPDATE {SCHEMA_NAME}.stock_companies SET description = NULL"
            cur.execute(sql)
            affected = cur.rowcount
            db.conn.commit()
            print(f"Reset {affected} descriptions in stock_companies.", flush=True)
            
    except Exception as e:
        print(f"Error resetting descriptions: {e}", flush=True)
        if db.conn:
            db.conn.rollback()
    finally:
        if db.conn:
            db.disconnect()

if __name__ == "__main__":
    print("Starting reset of KR descriptions...", flush=True)
    reset_descriptions()
