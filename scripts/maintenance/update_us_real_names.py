
import psycopg2
import sys
import os
import time

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME
from src.kis_client import KisApiClient

def update_real_names():
    print("Connecting to DB...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 1. 대상 종목 조회 (미국 주식 전체)
    cur.execute(f"SELECT stock_code, market_type, company_name FROM {SCHEMA_NAME}.us_stock_companies")
    rows = cur.fetchall()
    print(f"Total target stocks: {len(rows)}")
    
    kis = KisApiClient()
    # 토큰 미리 발급
    if not kis.get_access_token():
        print("Failed to get access token")
        return

    updates = []
    
    print("Fetching Korean names from KIS API...")
    for i, row in enumerate(rows):
        code = row[0]
        market = row[1] # NAS, NYS, AMS 등
        
        # API 호출 (시장 코드 매핑 필요할 수 있음)
        # KisApiClient.get_overseas_stock_info는 market_code 인자를 받음 (NAS, NYS, AMS, HKS, SHS, SZS, TWS, VNS)
        # DB의 market_type이 API와 호환되는지 확인 필요. 보통 NAS, NYS는 맞음.
        
        target_market = market
        if not target_market:
            # 시장 정보 없으면 NYS/NAS 둘 다 시도? 일단 NYS 먼저
            target_market = "NAS" 
            
        info = kis.get_overseas_stock_info(code, target_market)
        
        # 만약 NAS로 안 되면 NYS로 재시도 (혹은 반대)
        if not info and target_market == "NAS":
             info = kis.get_overseas_stock_info(code, "NYS")
        elif not info and target_market == "NYS":
             info = kis.get_overseas_stock_info(code, "NAS")
             
        if info:
            korean_name = info.get('name')
            # API에서 한글명이 없거나 이상하면 건너뜀
            if korean_name:
                updates.append((korean_name, code))
                if i % 10 == 0:
                    print(f"  [{i+1}/{len(rows)}] {code}: {korean_name}")
        else:
            print(f"  [{i+1}/{len(rows)}] {code}: Failed to find info")
            
        # API Rate Limit 고려 (0.1초 대기)
        time.sleep(0.1)

    if updates:
        print(f"Updating {len(updates)} records in DB...")
        try:
            sql = f"UPDATE {SCHEMA_NAME}.us_stock_companies SET korean_name = %s WHERE stock_code = %s"
            from psycopg2.extras import execute_batch
            execute_batch(cur, sql, updates)
            conn.commit()
            print("Update complete.")
        except Exception as e:
            print(f"DB Update failed: {e}")
            conn.rollback()
    else:
        print("No updates found.")

    conn.close()

if __name__ == "__main__":
    update_real_names()
