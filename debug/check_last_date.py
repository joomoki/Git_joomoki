import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME

def check_last_date():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        with db.conn.cursor() as cur:
            # 1. Korea Stocks (daily_price)
            cur.execute(f"SELECT MAX(trade_date) FROM {SCHEMA_NAME}.daily_price")
            kr_last_date = cur.fetchone()[0]
            print(f"Korea Stock Last Date (daily_price): {kr_last_date}")

            # 2. US Stocks (us_stock_prices)
            cur.execute(f"SELECT MAX(trade_date) FROM {SCHEMA_NAME}.us_stock_prices")
            us_last_date = cur.fetchone()[0]
            print(f"US Stock Last Date (us_stock_prices): {us_last_date}")

    except Exception as e:
        print(f"Error checking last date: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    check_last_date()
