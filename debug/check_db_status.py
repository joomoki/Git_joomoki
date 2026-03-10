import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.stock_db_manager import StockDBManager

def check_status():
    db = StockDBManager()
    try:
        with db.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM us_stock_companies")
            us_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM stock_companies")
            kr_count = cur.fetchone()[0]
            
            print(f"US Stocks in DB: {us_count}")
            print(f"KR Stocks in DB: {kr_count}")
            
            if us_count > 0:
                cur.execute("SELECT stock_code, company_name FROM us_stock_companies LIMIT 5")
                print("Sample US Stocks:", cur.fetchall())
                
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check_status()
