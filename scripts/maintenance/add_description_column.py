
import psycopg2
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

def add_description_column():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # Domestic stocks
        print("Adding description column to stock_companies...")
        cur.execute(f"""
            ALTER TABLE {SCHEMA_NAME}.stock_companies 
            ADD COLUMN IF NOT EXISTS description TEXT;
        """)
        
        # US stocks
        print("Adding description column to us_stock_companies...")
        cur.execute(f"""
            ALTER TABLE {SCHEMA_NAME}.us_stock_companies 
            ADD COLUMN IF NOT EXISTS description TEXT;
        """)
        
        conn.commit()
        print("Successfully added description columns.")
        
    except Exception as e:
        print(f"Error adding description column: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_description_column()
