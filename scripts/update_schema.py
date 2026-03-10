import sys
import os
import psycopg2

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG

def update_schema():
    print("=== DB 스키마 업데이트 시작 ===")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # SQL 파일 읽기
        sql_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sql', 'create_stock_schema.sql')
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
            
        # SQL 실행
        cur.execute(sql)
        conn.commit()
        print("스키마 업데이트 성공")
        
    except Exception as e:
        print(f"스키마 업데이트 실패: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    update_schema()
