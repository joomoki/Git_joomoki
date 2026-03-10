
import psycopg2
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

def check_korean_names():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("Checking us_stock_companies for missing korean_names...")
    
    cur.execute(f"""
        SELECT count(*) 
        FROM {SCHEMA_NAME}.us_stock_companies 
        WHERE korean_name IS NULL OR korean_name = '' OR korean_name = company_name
    """)
    missing_count = cur.fetchone()[0]
    
    cur.execute(f"""
        SELECT count(*) 
        FROM {SCHEMA_NAME}.us_stock_companies 
    """)
    total_count = cur.fetchone()[0]
    
    print(f"Total US Stocks: {total_count}")
    print(f"Stocks needing translation: {missing_count}")
    
    if missing_count > 0:
        print("Sample needing translation:")
        cur.execute(f"""
            SELECT stock_code, company_name, korean_name
            FROM {SCHEMA_NAME}.us_stock_companies 
            WHERE korean_name IS NULL OR korean_name = '' OR korean_name = company_name
            LIMIT 5
        """)
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} (Current KR: {row[2]})")

    conn.close()

if __name__ == "__main__":
    check_korean_names()
