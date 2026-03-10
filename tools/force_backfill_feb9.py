import sys
import os
import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager
from src.export_to_web import export_history_data

def force_backfill():
    print("=== Force Backfill for Feb 9 & 10 ===")
    
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    target_dates = ['2026-02-09', '2026-02-10']
    
    # 7 priority stocks
    # ('067900', '와이엔텍')
    # ('137940', '넥스트아이')
    # ('010690', '화신')
    # ('005440', '현대지에프홀딩스')
    # ('059100', '아이컴포넌트')
    # ('080530', '코디')
    # ('017670', 'SK텔레콤')
    
    target_stocks = ['067900', '137940', '010690', '005440', '059100', '080530', '017670']

    try:
        for date_str in target_dates:
            print(f"\nProcessing {date_str}...")
            count = 0
            for code in target_stocks:
                # 1. Get price for that date
                with db.conn.cursor() as cur:
                    cur.execute(f"SELECT close_price FROM joomoki_news.stock_prices WHERE stock_code = %s AND trade_date = %s", (code, date_str))
                    row = cur.fetchone()
                    
                if row:
                    price = float(row[0])
                    # 2. Save history (Force score 90)
                    # save_recommendation_history(self, stock_code, date, price, score, is_us=False)
                    if db.save_recommendation_history(code, date_str, price, 90, is_us=False):
                        count += 1
                        print(f"  Saved {code} at {price}")
                else:
                    print(f"  No price for {code} on {date_str}")
            
            print(f"  Total saved for {date_str}: {count}")

        # Export
        print("\nExporting history data...")
        export_history_data(db, 'd:/joomoki_PJ/stock_portal_joomoki/data')
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.disconnect()
        print("=== Completed ===")

if __name__ == "__main__":
    force_backfill()
