
import sys
import os
import psycopg2

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME

def check_tables():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Check if schema exists
        cur.execute(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{SCHEMA_NAME}';")
        if not cur.fetchone():
            print(f"Schema '{SCHEMA_NAME}' does not exist.")
            return

        # List tables in schema
        cur.execute(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{SCHEMA_NAME}';
        """)
        
        tables = cur.fetchall()
        print(f"Schema '{SCHEMA_NAME}' tables:")
        if not tables:
            print("No tables found.")
        for table in tables:
            print(f"- {table[0]}")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error checking tables: {e}")

if __name__ == "__main__":
    check_tables()
