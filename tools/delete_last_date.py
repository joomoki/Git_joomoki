import sys
import os
import psycopg2

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.db_config import DB_CONFIG, SCHEMA_NAME

def delete_last_date(target_date="2026-02-20"):
    print(f"=== {target_date} 주식 데이터 삭제 스크립트 ===")
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. 국내 주식 삭제
        print(f"[한국 주식] {target_date} 데이터 삭제 중...")
        kr_queries = [
            f"DELETE FROM {SCHEMA_NAME}.daily_price WHERE trade_date = %s",
            f"DELETE FROM {SCHEMA_NAME}.stock_prices WHERE trade_date = %s",
            f"DELETE FROM {SCHEMA_NAME}.stock_analysis WHERE analysis_date = %s",
            f"DELETE FROM {SCHEMA_NAME}.stock_investor_trends WHERE trade_date = %s",
            f"DELETE FROM {SCHEMA_NAME}.stock_recommendation_history WHERE recommendation_date = %s AND is_us = FALSE"
        ]
        
        for q in kr_queries:
            cur.execute(q, (target_date,))
            print(f"  - Executed: {q.split('WHERE')[0].strip()} (= {target_date})")

        # 2. 미국 주식 삭제
        print(f"\n[미국 주식] {target_date} 데이터 삭제 중...")
        us_queries = [
            f"DELETE FROM {SCHEMA_NAME}.us_stock_prices WHERE trade_date = %s",
            f"DELETE FROM {SCHEMA_NAME}.us_stock_analysis WHERE analysis_date = %s",
            f"DELETE FROM {SCHEMA_NAME}.us_stock_news WHERE news_date::date = %s",
            f"DELETE FROM {SCHEMA_NAME}.stock_recommendation_history WHERE recommendation_date = %s AND is_us = TRUE"
        ]
        
        for q in us_queries:
            cur.execute(q, (target_date,))
            print(f"  - Executed: {q.split('WHERE')[0].strip()} (= {target_date})")

        conn.commit()
        print("\n[SUCCESS] 데이터 삭제가 정상적으로 완료되었습니다.")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"[ERROR] DB 오류 발생: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == '__main__':
    # 날짜를 변경하려면 인자로 전달 가능
    target = "2026-02-20"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    delete_last_date(target)
