import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME
from src.export_to_web import export_history_data

def manage_history():
    print("=== Manage Recommendation History (Delete Feb 18, Add Feb 12) ===")
    
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        # 1. Delete Feb 18
        print("\n[Deleting 2026-02-18 Data]")
        with db.conn.cursor() as cur:
            cur.execute(f"DELETE FROM {SCHEMA_NAME}.stock_recommendation_history WHERE recommendation_date = '2026-02-18'")
            deleted_count = cur.rowcount
            print(f"  Deleted {deleted_count} rows.")
        db.conn.commit()

        # 2. Add Feb 12
        # Target stocks (same as force backfill)
        target_stocks = ['067900', '137940', '010690', '005440', '059100', '080530', '017670']
        date_str = '2026-02-12'
        
        print(f"\n[Adding {date_str} Data]")
        count = 0
        for code in target_stocks:
             # Get price
             with db.conn.cursor() as cur:
                cur.execute(f"SELECT close_price FROM {SCHEMA_NAME}.stock_prices WHERE stock_code = %s AND trade_date = %s", (code, date_str))
                row = cur.fetchone()
             
             if row:
                 price = float(row[0])
                 # Save history (Force score 90)
                 if db.save_recommendation_history(code, date_str, price, 90, is_us=False): 
                     count += 1
                     print(f"  Saved {code} at {price}")
             else:
                 print(f"  No price for {code} on {date_str}")
        
        print(f"  Total added for {date_str}: {count}")
        
        # 3. Export
        print("\n[Exporting Data]")
        export_history_data(db, 'd:/joomoki_PJ/stock_portal_joomoki/data')
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.conn.rollback()
    
    finally:
        db.disconnect()
        print("\n=== Completed ===")

if __name__ == "__main__":
    manage_history()
