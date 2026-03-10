import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager
from src.kis_client import KisApiClient
from config.db_config import SCHEMA_NAME

def backfill_missing_data():
    """
    2월 16, 17, 18일 누락 데이터를 채운다.
    (kis_client.get_daily_price 사용 -> 최근 30일치 가져옴)
    이미 있는 날짜(19일, 13일 이전)는 무시하고, 없는 날짜만 daily_price에 insert.
    """
    print("=== Backfill Missing Data (Feb 16-18) ===")
    
    db = StockDBManager()
    if not db.connect():
        print("DB fail")
        return
        
    kis = KisApiClient()
    
    try:
        # 모든 종목 코드 가져오기
        with db.conn.cursor() as cur:
            # DEBUG: LIMIT 제거
            cur.execute(f"SELECT stock_code FROM {SCHEMA_NAME}.stock_companies WHERE market_type IN ('KOSPI', 'KOSDAQ')")
            stocks = cur.fetchall()
        print(f"Total stocks to check: {len(stocks)}")
        
        count = 0
        
        # Insert Query (daily_price)
        # Table Columns: stock_code, trade_date, open_price, high_price, low_price, close_price, volume, amount
        insert_sql = f"""
            INSERT INTO {SCHEMA_NAME}.daily_price 
            (stock_code, trade_date, open_price, high_price, low_price, close_price, volume, amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (stock_code, trade_date) DO NOTHING
        """
        
        with db.conn.cursor() as cur:
            for i, s in enumerate(stocks):
                code = s[0]
                
                # API 호출 (최근 일별 시세)
                data = kis.get_daily_price(code) 
                
                if not data:
                    print(f"[{i+1}/{len(stocks)}] No data from API for {code}")
                    time.sleep(0.05)
                    continue
                
                inserted_count = 0
                for row in data:
                    date_str = row['stck_bsop_date']
                    date_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}" # YYYY-MM-DD
                    
                    if date_str in ['20260216', '20260217', '20260218', '20260219']:
                        try:
                            # 데이터 검증 (None 체크)
                            if row['stck_clpr']:
                                # API: acml_tr_pbmn = 거래대금 (amount)
                                amount = float(row.get('acml_tr_pbmn', 0))
                                
                                cur.execute(insert_sql, (code, date_fmt, float(row['stck_oprc']), float(row['stck_hgpr']), 
                                                         float(row['stck_lwpr']), float(row['stck_clpr']), int(row['acml_vol']), 
                                                         amount))
                                inserted_count += 1
                        except Exception as e:
                            print(f"  Insert failed for {code} on {date_fmt}: {e}")
                            db.conn.rollback()

                if inserted_count > 0:
                     # print(f"  Inserted {inserted_count} rows for {code}")
                     pass
                
                count += 1
                if count % 100 == 0:
                    db.conn.commit()
                    print(f"Processed {count}/{len(stocks)} stocks...")
                
                time.sleep(0.05)
                
            db.conn.commit()
            print("Backfill Completed.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.conn.rollback()
    finally:
        db.disconnect()

if __name__ == "__main__":
    backfill_missing_data()
