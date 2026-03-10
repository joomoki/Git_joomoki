import sys
import os
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager

def update_priority_prices():
    print("=== 우선순위 종목 주가 업데이트 시작 ===")
    
    db_manager = StockDBManager()
    if not db_manager.connect():
        print("DB 연결 실패")
        return

    # 업데이트할 종목 코드 리스트 (사용자 화면에 노출된 종목들)
    target_stocks = [
        ('067900', '와이엔텍'),
        ('137940', '넥스트아이'),
        ('010690', '화신'),
        ('005440', '현대지에프홀딩스'),
        ('059100', '아이컴포넌트'),
        ('080530', '코디'),
        ('017670', 'SK텔레콤')
    ]

    try:
        success_count = 0
        
        # 날짜 설정
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        
        for stock_code, name in target_stocks:
            print(f"\nProcessing {name} ({stock_code})...")
            
            # 마지막 수집일 확인
            # last_date = db_manager.get_last_price_date(stock_code) # 메서드 있는지 불확실하므로 직접 쿼리
            
            # start_date = '2026-02-11' # 문제의 날짜부터 다시 수집
            start_date = '2025-01-01'
            
            print(f"  Fetching from {start_date} to {end_date}")
            
            df = fdr.DataReader(stock_code, start_date, end_date)
            
            if df.empty:
                print("  No data found.")
                continue

            price_data = []
            for date_idx, row in df.iterrows():
                trade_date = date_idx.strftime('%Y-%m-%d')
                row = row.fillna(0)
                
                price_tuple = (
                    trade_date,
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    int(row['Volume']),
                    0 
                )
                price_data.append(price_tuple)
            
            # DB 저장 (insert_price_list 사용)
            # 만약 StockDBManager에 insert_price_list가 없다면 에러 날 것임 -> 그때 확인
            if hasattr(db_manager, 'insert_price_list'):
                 if db_manager.insert_price_list(stock_code, price_data):
                    print(f"  Saved {len(price_data)} records.")
                    success_count += 1
            else:
                # 직접 쿼리 실행
                print("  insert_price_list method not found. Using direct SQL.")
                with db_manager.conn.cursor() as cur:
                    sql = f"""
                        INSERT INTO stock_db.stock_prices (trade_date, open_price, high_price, low_price, close_price, volume, market_cap, stock_code)
                        VALUES %s
                        ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED.volume
                    """
                    # execute_values를 위해 데이터 구조 변경 필요할 수 있음
                    # (trade_date, open, high, low, close, volume, market_cap) + stock_code
                    values = [p + (stock_code,) for p in price_data]
                    
                    from psycopg2.extras import execute_values
                    execute_values(cur, sql, values)
                    db_manager.conn.commit()
                    print(f"  Saved {len(price_data)} records (Direct SQL).")
                    success_count += 1

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_manager.disconnect()

if __name__ == "__main__":
    update_priority_prices()
