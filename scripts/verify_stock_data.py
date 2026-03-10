import psycopg2
import sys
import os
import pprint

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

def verify_data():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"=== {SCHEMA_NAME}.stock_companies 조회 ===")
        cur.execute(f"SELECT * FROM {SCHEMA_NAME}.stock_companies WHERE stock_code = '005930';")
        company = cur.fetchone()
        print(company)
        
        print(f"\n=== {SCHEMA_NAME}.stock_prices 조회 (최근 5건) ===")
        cur.execute(f"SELECT * FROM {SCHEMA_NAME}.stock_prices WHERE stock_code = '005930' ORDER BY trade_date DESC LIMIT 5;")
        prices = cur.fetchall()
        pprint.pprint(prices)
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    verify_data()
