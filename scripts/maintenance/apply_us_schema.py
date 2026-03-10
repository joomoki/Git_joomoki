import psycopg2
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG

def apply_schema():
    try:
        print(f"Connecting to database '{DB_CONFIG['database']}'...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sql_file_path = os.path.join(base_dir, 'sql', 'create_us_stock_schema.sql')
        print(f"Reading SQL file: {sql_file_path}")
    
    # 2. SQL 파일 읽기 (UTF-8)
    # 기존 create_us_stock_schema.sql 대신 add_columns_us_stock.sql 실행하여 컬럼 추가 반영
        alter_sql_path = os.path.join(base_dir, 'sql', 'add_columns_us_stock.sql')
        if os.path.exists(alter_sql_path):
            print(f"Reading Alter SQL file: {alter_sql_path}")
            with open(alter_sql_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
        else:
            # fallback
            print(f"Alter SQL file not found, falling back to: {sql_file_path}")
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
        print("Executing SQL...")
        cur.execute(sql_script)
        conn.commit()
        
        print("[SUCCESS] US Stock Schema applied successfully!")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to apply schema: {e}")
        return False

if __name__ == "__main__":
    apply_schema()
