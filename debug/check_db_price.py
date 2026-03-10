
import psycopg2
import sys
import os
import json

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME

def check_price_data(stock_code):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"Checking data for {stock_code} in {SCHEMA_NAME}.daily_price...")
        
        # 1. Count
        sql_count = f"SELECT count(*) FROM {SCHEMA_NAME}.daily_price WHERE stock_code = %s"
        cur.execute(sql_count, (stock_code,))
        count = cur.fetchone()[0]
        print(f"  - Total rows: {count}")
        
        # 2. Recent 5 rows
        sql_recent = f"""
            SELECT trade_date, close_price 
            FROM {SCHEMA_NAME}.daily_price 
            WHERE stock_code = %s 
            ORDER BY trade_date DESC 
            LIMIT 5
        """
        cur.execute(sql_recent, (stock_code,))
        rows = cur.fetchall()
        print("  - Recent 5 rows:")
        for r in rows:
            print(f"    {r}")
            
        # 3. Check if partitions exist (optional, but good to know)
        # This query checks if the query planner scans partitions for a date range
        # simpler: just check if data exists for a specific recent date
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # SK Telecom
    check_price_data('017670') 
