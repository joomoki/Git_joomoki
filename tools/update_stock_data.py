import sys
import os
import time
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager
from src.kis_client import KisApiClient
from src.stock_updater_logic import StockUpdater
from config.db_config import SCHEMA_NAME
import backfill_history
from src import export_to_web

def get_latest_trade_date(db):
    """DB에서 가장 최신 거래일 조회"""
    with db.conn.cursor() as cur:
        # daily_price와 stock_prices 중 더 최신 날짜 확인
        sql = f"""
            SELECT MAX(trade_date) FROM (
                SELECT MAX(trade_date) as trade_date FROM {SCHEMA_NAME}.daily_price
                UNION ALL
                SELECT MAX(trade_date) as trade_date FROM {SCHEMA_NAME}.stock_prices
            ) u
        """
        cur.execute(sql)
        row = cur.fetchone()
        return row[0] if row and row[0] else None

def update_stock_data():
    print("=== Update Stock Data (Auto) ===")
    
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        # 0. 객체 초기화
        kis = KisApiClient()
        updater = StockUpdater(db, kis)

        # 1. 최신 데이터 날짜 확인
        last_date = get_latest_trade_date(db)
        print(f"Latest DB Date: {last_date}")
        
        today = datetime.now().date()
        target_dates = []
        
        if last_date:
            # 마지막 데이터 다음날부터 오늘까지
            start_dt = last_date + timedelta(days=1)
            delta = (today - start_dt).days
            for i in range(delta + 1):
                d = start_dt + timedelta(days=i)
                # 주말 제외 (토=5, 일=6)
                if d.weekday() < 5:
                    target_dates.append(d.strftime("%Y%m%d"))
        else:
            # 데이터가 없으면 오늘만
            if today.weekday() < 5:
                target_dates.append(today.strftime("%Y%m%d"))
        
        print(f"Dates to update: {target_dates}")
        
        if not target_dates:
            print("Everything is up-to-date.")
            # 강제로 오늘 점수 재계산이라도 할지 결정 필요
            # return 
        
        # 2. 데이터 수집
        if target_dates:
            print("\n--- Fetching & Inserting Daily Prices ---")
            updater.update_daily_prices(target_dates)
        
        # 3. 점수 재계산 (최근 5일치)
        print("\n--- Recalculating AI Scores ---")
        # backfill_history를 모듈로 불러와서 실행하거나 로직 복사
        # 여기서는 간단히 subprocess로 호출하거나 함수를 import해서 사용
        # backfill_history.py 의 메인 함수를 리팩토링해서 호출하는 것이 좋으나, 
        # 일단 import 된 backfill_history 의 함수를 사용하는 식으로 가정 (현재는 main만 있음)
        # 임시로 os.system 사용 (가상환경 주의)
        os.system(f"python {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backfill_history.py')}")
        
        # 4. 웹 내보내기
        print("\n--- Exporting to Web ---")
        export_to_web.export_data() # export_to_web.py 에 main 로직을 함수화해야 함. 현재는 없음.
        # 따라서 os.system 사용
        os.system(f"python {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'export_to_web.py')}")
        
        print("\n[SUCCESS] All updates completed.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()

if __name__ == "__main__":
    update_stock_data()
