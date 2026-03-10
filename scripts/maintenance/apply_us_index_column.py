import psycopg2
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG

def apply_column():
    try:
        print(f"Connecting to database '{DB_CONFIG['database']}'...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sql_file_path = os.path.join(base_dir, 'sql', 'add_index_column_us.sql')
        
        print(f"Reading SQL file: {sql_file_path}")
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        print("Executing SQL...")
        cur.execute(sql_script)
        conn.commit()
        
        print("[SUCCESS] Major Index column added successfully!")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to add column: {e}")
        return False

if __name__ == "__main__":
    apply_column()
