import psycopg2
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

def verify_count():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.stock_companies;")
        count = cur.fetchone()[0]
        print(f"Total Stock Companies in DB: {count}")

        # Check a sample
        cur.execute(f"SELECT * FROM {SCHEMA_NAME}.stock_companies LIMIT 1;")
        sample = cur.fetchone()
        print(f"Sample data: {sample}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    verify_count()
