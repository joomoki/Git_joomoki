
import psycopg2
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME

def reset_corrupted_data():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. 노키아(ADR) 초기화
        print("Resetting '노키아(ADR)'...")
        cur.execute(f"UPDATE {SCHEMA_NAME}.us_stock_companies SET korean_name = NULL WHERE korean_name LIKE '%노키아(ADR)%'")
        print(f"  - {cur.rowcount} rows updated.")
        
        # 2. 아레스 캐피탈 등 중복 초기화 (count > 10 인것들)
        print("Resetting identifying duplicates...")
        sql = f"""
            UPDATE {SCHEMA_NAME}.us_stock_companies
            SET korean_name = NULL
            WHERE korean_name IN (
                SELECT korean_name
                FROM {SCHEMA_NAME}.us_stock_companies
                WHERE korean_name IS NOT NULL
                GROUP BY korean_name
                HAVING COUNT(*) > 5
            )
        """
        cur.execute(sql)
        print(f"  - {cur.rowcount} duplicate rows updated.")
        
        conn.commit()
        conn.close()
        print("Data reset complete.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_corrupted_data()
