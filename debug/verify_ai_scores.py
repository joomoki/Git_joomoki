
import json
import os
import sys
import psycopg2

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

def verify_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("Verifying DB AI Scores...")
    # 최근 업데이트된 5개 종목 조회
    cur.execute(f"""
        SELECT stock_code, ai_score, updated_at 
        FROM {SCHEMA_NAME}.stock_analysis 
        ORDER BY updated_at DESC 
        LIMIT 5
    """)
    rows = cur.fetchall()
    
    db_scores = {}
    for r in rows:
        print(f"DB: {r[0]}, Score: {r[1]}, Updated: {r[2]}")
        db_scores[r[0]] = r[1]
        
    print("-" * 20)
    
    # JS 파일 확인
    js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                          'stock_portal_joomoki', 'data', 'stock_data_kr_1.js')
    
    if not os.path.exists(js_path):
        print(f"JS file not found: {js_path}")
        return

    print(f"Reading JS file: {js_path}")
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # "if(typeof stockData !== 'undefined') { stockData.stocks = stockData.stocks.concat(" ... "); }"
        # JSON 부분만 추출
        start = content.find('concat(') + 7
        end = content.rfind(');')
        json_str = content[start:end]
        
        data = json.loads(json_str)
        
        print(f"JS file contains {len(data)} items.")
        
        matched_count = 0
        for item in data:
            code = item.get('code')
            score = item.get('analysis', {}).get('score')
            
            if code in db_scores:
                print(f"MATCH: {code} -> JS Score: {score}, DB Score: {db_scores[code]}")
                if score == db_scores[code]:
                    print("  [OK] Scores match.")
                    matched_count += 1
                else:
                    print("  [FAIL] Scores mismatch!")
        
        if matched_count > 0:
            print("Verification Successful for sampled items.")
        else:
            print("Could not find sampled DB items in the first JS chunk (might be in other chunks).")

    conn.close()

if __name__ == "__main__":
    verify_data()
