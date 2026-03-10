import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager, SCHEMA_NAME

def check_status():

    db = StockDBManager()
    if not db.connect():
        print("DB Connection failed")
        return

    try:
        with db.conn.cursor() as cur:
            # Check KR
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.stock_companies WHERE description IS NOT NULL AND description != ''")
            kr_filled = cur.fetchone()[0]
            
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.stock_companies")
            kr_total = cur.fetchone()[0]
            
            print(f"KR Stock Descriptions: {kr_filled} / {kr_total} ({(kr_filled/kr_total)*100:.1f}%)")

            # Check US
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.us_stock_companies WHERE description IS NOT NULL AND description != ''")
            us_filled = cur.fetchone()[0]
            
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.us_stock_companies")
            us_total = cur.fetchone()[0]
            
            print(f"US Stock Descriptions: {us_filled} / {us_total} ({(us_filled/us_total)*100:.1f}%)")
                
    except Exception as e:
        print(f"Error checking DB: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    check_status()
