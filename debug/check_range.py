import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME

def check_range():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        with db.conn.cursor() as cur:
            cur.execute(f"SELECT MIN(trade_date), MAX(trade_date), COUNT(*) FROM {SCHEMA_NAME}.daily_price")
            min_date, max_date, count = cur.fetchone()
            print(f"daily_price Range: {min_date} ~ {max_date} (Total: {count})")
            
            cur.execute(f"SELECT MIN(trade_date), MAX(trade_date), COUNT(*) FROM {SCHEMA_NAME}.stock_prices")
            min_date, max_date, count = cur.fetchone()
            print(f"stock_prices Range: {min_date} ~ {max_date} (Total: {count})")

    except Exception as e:
        print(f"Error checking range: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    check_range()
