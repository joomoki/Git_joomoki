
import psycopg2
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME

def check_old_price_data(stock_code):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Check stock_prices table
        print(f"Checking data for {stock_code} in {SCHEMA_NAME}.stock_prices...")
        try:
            sql_count = f"SELECT count(*) FROM {SCHEMA_NAME}.stock_prices WHERE stock_code = %s"
            cur.execute(sql_count, (stock_code,))
            count = cur.fetchone()[0]
            print(f"  - Total rows: {count}")
            
            if count > 0:
                sql_recent = f"""
                    SELECT stock_date, close_price 
                    FROM {SCHEMA_NAME}.stock_prices 
                    WHERE stock_code = %s 
                    ORDER BY stock_date DESC 
                    LIMIT 5
                """
                cur.execute(sql_recent, (stock_code,))
                rows = cur.fetchall()
                print("  - Recent 5 rows:")
                for r in rows:
                    print(f"    {r}")
        except Exception as e:
            print(f"  - stock_prices table might not exist or error: {e}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_old_price_data('017670')
