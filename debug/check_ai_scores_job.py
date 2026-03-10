import sys
import os
import psycopg2
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.db_config import DB_CONFIG, SCHEMA_NAME

def check_ai_scores():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("=== 국내 주식 AI 점수 현황 ===")
    cur.execute(f"SELECT analysis_date, COUNT(*), MAX(ai_score), MIN(ai_score) FROM {SCHEMA_NAME}.stock_analysis WHERE ai_score > 0 GROUP BY analysis_date ORDER BY analysis_date DESC LIMIT 5;")
    for row in cur.fetchall():
        print(row)
        
    print("\n=== 미국 주식 AI 점수 현황 ===")
    cur.execute(f"SELECT analysis_date, COUNT(*), MAX(ai_score), MIN(ai_score) FROM {SCHEMA_NAME}.us_stock_analysis WHERE ai_score > 0 GROUP BY analysis_date ORDER BY analysis_date DESC LIMIT 5;")
    for row in cur.fetchall():
        print(row)
        
    conn.close()

if __name__ == '__main__':
    check_ai_scores()
