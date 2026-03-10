import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager, SCHEMA_NAME

def check_encoding():
    db = StockDBManager()
    if not db.connect():
        return

    try:
        with db.conn.cursor() as cur:
            # Check Samsung Electronics 005930
            cur.execute(f"SELECT company_name, description FROM {SCHEMA_NAME}.stock_companies WHERE stock_code = '005930'")
            row = cur.fetchone()
            if row:
                print(f"[{row[0]}] Description:")
                print(row[1][:200])
            else:
                print("Samsung Electronics not found.")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    check_encoding()
