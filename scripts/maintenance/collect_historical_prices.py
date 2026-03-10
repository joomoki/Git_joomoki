import sys
import os
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
import time

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager

def collect_historical_prices():
    print("=== 국내 전종목 최근 1년 주가 수집 시작 ===")
    
    db_manager = StockDBManager()
    if not db_manager.connect():
        print("DB 연결 실패")
        return

    try:
        # 1. 수집 대상 종목 가져오기
        stocks = db_manager.get_all_stocks()
        total_stocks = len(stocks)
        print(f"총 {total_stocks}개 종목에 대한 데이터 수집을 시작합니다.")

        # 2. 날짜 설정 (최근 1년은 기본값)
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        default_start_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # print(f"수집 기간: {start_date} ~ {end_date}") <- 종목별로 다르므로 제거


        success_count = 0
        error_count = 0
        
        # 3. 종목별 수집 및 저장
        for i, (stock_code, market_type, company_name) in enumerate(stocks):
            try:
                # 마지막 수집일 확인
                last_date = db_manager.get_last_price_date(stock_code)
                
                if last_date:
                    # 마지막 날짜 다음날부터 수집
                    start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                else:
                    # 데이터 없으면 기본 1년치
                    start_date = default_start_date

                # 시작일이 종료일보다 미래면 스킵 (이미 최신)
                if start_date > end_date:
                    continue

                # 진행 상황 출력
                if i % 10 == 0:
                    print(f"[{i+1}/{total_stocks}] 진행 중... (성공: {success_count}, 실패: {error_count})")

                print(f"[{stock_code}] 수집 기간: {start_date} ~ {end_date}")

                # 데이터 다운로드
                df = fdr.DataReader(stock_code, start_date, end_date)
                
                if df.empty:
                    # 데이터가 없는 경우 (상장폐지, 코드 변경 등)
                    error_count += 1
                    continue

                # 데이터 변환 (DataFrame -> List of Tuples)
                # target format: (trade_date, open, high, low, close, volume, market_cap)
                price_data = []
                for date_idx, row in df.iterrows():
                    # FinanceDataReader 컬럼: Open, High, Low, Close, Volume, Change
                    # Market Cap은 시세 데이터에는 포함되지 않는 경우가 많음 (StockListing에는 있음)
                    # 여기서는 Market Cap을 0 또는 None으로 처리하거나, 별도 계산 필요.
                    # 일단 0으로 저장하고 향후 업데이트 고려.
                    
                    trade_date = date_idx.strftime('%Y-%m-%d')
                    
                    # NaN 값 처리
                    row = row.fillna(0)
                    
                    price_tuple = (
                        trade_date,
                        float(row['Open']),
                        float(row['High']),
                        float(row['Low']),
                        float(row['Close']),
                        int(row['Volume']),
                        0 # Market Cap (Daily info not provided by FDR basic reader)
                    )
                    price_data.append(price_tuple)

                # DB 저장
                if db_manager.insert_price_list(stock_code, price_data):
                    success_count += 1
                else:
                    error_count += 1
                
                # 너무 빠른 요청 방지를 위한 미세 딜레이 (선택적)
                # time.sleep(0.01) 

            except Exception as e:
                print(f"실패 [{stock_code} {company_name}]: {e}")
                error_count += 1

        print(f"\n[완료] 총 {total_stocks}개 중 성공: {success_count}, 실패: {error_count}")

    except Exception as e:
        print(f"\n치명적 에러 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_manager.disconnect()
        print("=== 작업 종료 ===")

if __name__ == "__main__":
    collect_historical_prices()
