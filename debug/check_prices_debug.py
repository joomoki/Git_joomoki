import sys
import os
import psycopg2
from datetime import datetime, timedelta

# 상위 디렉토리 경로 추가 (config 모듈 import 위함)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.db_config import DB_CONFIG, SCHEMA_NAME

def check_prices():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. 최근 trade_date 조회 (국내)
        print("Checking Korea Stock Prices...")
        cur.execute(f"SELECT DISTINCT trade_date FROM {SCHEMA_NAME}.stock_prices ORDER BY trade_date DESC LIMIT 10")
        dates = cur.fetchall()
        print("Recent Korea Stock Dates:", [d[0].strftime('%Y-%m-%d') for d in dates])
        
        # 2. 특정 종목(예: 와이엔텍 067900)의 2월 11일 이후 데이터 조회
        target_code = '067900'
        target_date = '2026-02-09'
        print(f"\nChecking Prices for {target_code} since {target_date}...")
        cur.execute(f"""
            SELECT trade_date, close_price 
            FROM {SCHEMA_NAME}.stock_prices 
            WHERE stock_code = %s AND trade_date >= %s
            ORDER BY trade_date ASC
        """, (target_code, target_date))
        rows = cur.fetchall()
        for r in rows:
            print(f"  {r[0]}: {r[1]}")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    check_prices()
