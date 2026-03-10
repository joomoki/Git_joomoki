import sys
import os
import time
from datetime import datetime
from .stock_db_manager import StockDBManager
from .kis_client import KisApiClient
from config.db_config import SCHEMA_NAME

class StockUpdater:
    def __init__(self, db_manager: StockDBManager, kis_client: KisApiClient):
        self.db = db_manager
        self.kis = kis_client

    def update_daily_prices(self, target_dates: list):
        """
        지정된 날짜 리스트에 해당하는 일별 시세를 업데이트합니다.
        :param target_dates: ['YYYY-MM-DD', ...] or ['YYYYMMDD', ...]
        """
        if not target_dates:
            return

        # 날짜 포맷 통일 (API는 YYYYMMDD 반환)
        target_dates_str = [d.replace('-', '') for d in target_dates]
        print(f"Updating daily prices for dates: {target_dates_str}")

        # 모든 종목 코드 가져오기
        with self.db.conn.cursor() as cur:
            cur.execute(f"SELECT stock_code FROM {SCHEMA_NAME}.stock_companies WHERE market_type IN ('KOSPI', 'KOSDAQ')")
            stocks = cur.fetchall()
        
        print(f"Total stocks to check: {len(stocks)}")
        
        # Insert Query (daily_price)
        insert_sql = f"""
            INSERT INTO {SCHEMA_NAME}.daily_price 
            (stock_code, trade_date, open_price, high_price, low_price, close_price, volume, amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (stock_code, trade_date) DO NOTHING
        """
        
        with self.db.conn.cursor() as cur:
            count = 0
            for i, s in enumerate(stocks):
                code = s[0]
                
                try:
                    # API 호출 (최근 일별 시세)
                    data = self.kis.get_daily_price(code) 
                    
                    if not data:
                        # print(f"[{i+1}/{len(stocks)}] No data from API for {code}")
                        time.sleep(0.05)
                        continue
                    
                    inserted_count = 0
                    for row in data:
                        date_str = row['stck_bsop_date'] # YYYYMMDD
                        
                        if date_str in target_dates_str:
                            date_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}" # YYYY-MM-DD
                            
                            try:
                                if row['stck_clpr']:
                                    amount = float(row.get('acml_tr_pbmn', 0))
                                    cur.execute(insert_sql, (code, date_fmt, float(row['stck_oprc']), float(row['stck_hgpr']), 
                                                             float(row['stck_lwpr']), float(row['stck_clpr']), int(row['acml_vol']), 
                                                             amount))
                                    inserted_count += 1
                            except Exception as e:
                                print(f"  Insert failed for {code} on {date_fmt}: {e}")
                                self.db.conn.rollback()

                    count += 1
                    if count % 100 == 0:
                        self.db.conn.commit()
                        print(f"Processed {count}/{len(stocks)} stocks...")
                    
                    time.sleep(0.05) 
                    
                except Exception as e:
                    print(f"Error processing stock {code}: {e}")
                    # self.db.conn.rollback() # 커서 레벨에서 처리되거나 상위에서 처리
            
            self.db.conn.commit()
            print("Update Completed.")
