import sys
import os
import psycopg2

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME

def add_signals_column():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"Checking if 'signals' column exists in {SCHEMA_NAME}.stock_analysis...")
        
        # Check if column exists
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{SCHEMA_NAME}' 
            AND table_name = 'stock_analysis' 
            AND column_name = 'signals';
        """)
        
        if cur.fetchone():
            print("Column 'signals' already exists.")
        else:
            print("Adding 'signals' column...")
            cur.execute(f"ALTER TABLE {SCHEMA_NAME}.stock_analysis ADD COLUMN signals JSONB;")
            conn.commit()
            print("Column 'signals' added successfully.")
            
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_signals_column()
