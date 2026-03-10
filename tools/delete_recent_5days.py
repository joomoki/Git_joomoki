import sys
import os
import psycopg2

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.db_config import DB_CONFIG, SCHEMA_NAME

def delete_recent_5days():
    print("=== 최근 5영업일 주식 데이터 삭제 스크립트 ===")
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. 국내 주식 최근 5일 기준 날짜 확보 (stock_prices에서 가장 높은 5일 추출)
        cur.execute(f"SELECT DISTINCT trade_date FROM {SCHEMA_NAME}.stock_prices ORDER BY trade_date DESC LIMIT 5")
        kr_dates = [row[0] for row in cur.fetchall()]
        
        if kr_dates:
            min_kr_date = min(kr_dates)
            print(f"[한국 주식] 최근 5일 최소 날짜: {min_kr_date}")
            
            # 삭제 쿼리 리스트
            kr_queries = [
                f"DELETE FROM {SCHEMA_NAME}.daily_price WHERE trade_date >= %s",
                f"DELETE FROM {SCHEMA_NAME}.stock_prices WHERE trade_date >= %s",
                f"DELETE FROM {SCHEMA_NAME}.stock_analysis WHERE analysis_date >= %s",
                f"DELETE FROM {SCHEMA_NAME}.stock_investor_trends WHERE trade_date >= %s",
                f"DELETE FROM {SCHEMA_NAME}.stock_recommendation_history WHERE recommendation_date >= %s AND is_us = FALSE"
            ]
            
            for q in kr_queries:
                cur.execute(q, (min_kr_date,))
                print(f"  - Executed: {q.split('WHERE')[0].strip()} (>= {min_kr_date})")
        else:
            print("[한국 주식] 최근 날짜를 찾을 수 없습니다.")

        # 2. 미국 주식 최근 5일 기준 날짜 확보
        cur.execute(f"SELECT DISTINCT trade_date FROM {SCHEMA_NAME}.us_stock_prices ORDER BY trade_date DESC LIMIT 5")
        us_dates = [row[0] for row in cur.fetchall()]
        
        if us_dates:
            min_us_date = min(us_dates)
            print(f"\n[미국 주식] 최근 5일 최소 날짜: {min_us_date}")
            
            us_queries = [
                f"DELETE FROM {SCHEMA_NAME}.us_stock_prices WHERE trade_date >= %s",
                f"DELETE FROM {SCHEMA_NAME}.us_stock_analysis WHERE analysis_date >= %s",
                f"DELETE FROM {SCHEMA_NAME}.us_stock_news WHERE news_date >= %s",  # 뉴스는 datetime일 수 있음
                f"DELETE FROM {SCHEMA_NAME}.stock_recommendation_history WHERE recommendation_date >= %s AND is_us = TRUE"
            ]
            
            for q in us_queries:
                cur.execute(q, (min_us_date,))
                print(f"  - Executed: {q.split('WHERE')[0].strip()} (>= {min_us_date})")
        else:
            print("[미국 주식] 최근 날짜를 찾을 수 없습니다.")

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
    delete_recent_5days()
