import psycopg2
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

def check_price_count():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.stock_prices;")
        count = cur.fetchone()[0]
        
        cur.execute(f"SELECT COUNT(DISTINCT stock_code) FROM {SCHEMA_NAME}.stock_prices;")
        stock_count = cur.fetchone()[0]
        
        print(f"Total Price Rows: {count}")
        print(f"Stocks with Data: {stock_count}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Check failed: {e}")

if __name__ == "__main__":
    check_price_count()
