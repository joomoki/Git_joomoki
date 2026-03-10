import psycopg2
import sys
import os

# 프로젝트 루트 경로 추가 (scripts 폴더의 상위 폴더)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

def apply_schema():
    print("=== DB 스키마 및 주석 적용 시작 ===")
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # SQL 파일 읽기 (프로젝트 루트/sql)
        sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sql', 'apply_comments_and_schema.sql')
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql = f.read()
            
        # 스키마 치환 (혹시 sql 파일에 하드코딩 안되어 있다면 필요)
        # 현재 sql 파일은 public 스키마를 가정하거나 search_path 설정이 필요할 수 있음.
        # 안전하게 set search_path 실행
        cur.execute(f"SET search_path TO {SCHEMA_NAME}, public;")
        
        # SQL 실행
        cur.execute(sql)
        conn.commit()
        
        print("DB 스키마 및 주석이 성공적으로 적용되었습니다.")
        
    except Exception as e:
        print(f"스키마 적용 중 오류 발생: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    apply_schema()
