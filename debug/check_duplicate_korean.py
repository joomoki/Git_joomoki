
import psycopg2
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME

def check_duplicate_names():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("=== 한글명 중복 현황 (TOP 20) ===")
        sql = f"""
            SELECT korean_name, COUNT(*) as cnt
            FROM {SCHEMA_NAME}.us_stock_companies
            WHERE korean_name IS NOT NULL
            GROUP BY korean_name
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 20
        """
        cur.execute(sql)
        rows = cur.fetchall()
        
        for name, count in rows:
            print(f"{name}: {count}개 종목")
            
            # 해당 이름으로 된 종목 샘플 조회
            cur.execute(f"SELECT stock_code, company_name FROM {SCHEMA_NAME}.us_stock_companies WHERE korean_name = %s LIMIT 3", (name,))
            samples = cur.fetchall()
            for s in samples:
                print(f"  - {s[0]} ({s[1]})")

        print("\n=== '노키아(ADR)' 케이스 상세 조회 ===")
        sql_nokia = f"SELECT stock_code, company_name, market_type FROM {SCHEMA_NAME}.us_stock_companies WHERE korean_name LIKE '%노키아%'"
        cur.execute(sql_nokia)
        nokias = cur.fetchall()
        print(f"총 {len(nokias)}개 발견")
        for n in nokias[:10]:
            print(n)

        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_duplicate_names()
