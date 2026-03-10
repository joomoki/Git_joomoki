import sys
import os
import time
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kis_client import KisApiClient
from src.stock_db_manager import StockDBManager
from src.analysis.daily_analyzer import run_daily_analysis

def update_top_stocks():
    print("=== 시가총액 상위 50개 종목 데이터 업데이트 시작 ===")
    
    api_client = KisApiClient()
    db_manager = StockDBManager()
    
    if not db_manager.connect():
        print("DB 연결 실패")
        return

    try:
        # 1. 토큰 발급
        if not api_client.get_access_token():
            print("토큰 발급 실패")
            return

        # 2. 시가총액 상위 50개 종목 조회
        # get_market_stocks는 DB에 있는 종목을 가져옴. 
        # 만약 DB가 비어있다면, KIS API로 마스터 데이터를 가져와야 함.
        # 여기서는 DB에 마스터 데이터가 있다고 가정.
        print("상위 50개 종목 조회 중...")
        top_stocks = db_manager.get_market_stocks(limit=50, sort_by='market_cap')
        
        if not top_stocks:
            print("DB에 종목 정보가 없습니다. 마스터 데이터 업데이트가 필요할 수 있습니다.")
            print("KIS API를 통해 코스피/코스닥 전종목 마스터 다운로드 로직이 필요하나,")
            print("일단 scripts/save_stock_data.py 등을 통해 기본 종목이 저장되어 있는지 확인해주세요.")
            # 삼성전자는 저장되어 있을 것임.
            return

        print(f"업데이트 대상: {len(top_stocks)}개 종목")

        # 3. 각 종목별 일별 시세 업데이트
        for i, stock in enumerate(top_stocks):
            stock_code = stock[0]
            company_name = stock[1] # get_market_stocks query select order: stock_code, company_name, ...
            # 실제 쿼리는: stock_code, company_name, market_type... 순서가 아님.
            # get_market_stocks의 SQL SELECT: c.stock_code, c.company_name, ...
            # 2번째가 company_name 맞음.
            
            print(f"[{i+1}/{len(top_stocks)}] {company_name}({stock_code}) 업데이트 중...")
            
            # API 호출 (일별 시세)
            daily_prices = api_client.get_daily_price(stock_code)
            time.sleep(0.1) # API 제한 고려 (초당 20건 정도이나 안전하게)

            if daily_prices:
                # DB 저장
                db_manager.insert_daily_prices(stock_code, daily_prices)
                
                # 기본 정보(fundamentals)도 업데이트하면 좋음 (현재가 상세 조회 API 필요)
                # 여기서는 시간 관계상 일별 시세만 업데이트.
            else:
                print(f"  -> 데이터 수신 실패")

        print("=== 데이터 업데이트 완료 ===")
        
        # 4. 분석 실행
        # 상위 50개 종목에 대헤서만 분석을 돌리고 싶지만, run_daily_analysis는 전체를 돌림.
        # 일단 전체 분석 실행 (50개면 금방 끝남)
        print("=== 기술적 분석 실행 ===")
        run_daily_analysis() # 이 함수는 DB의 모든 종목을 스캔함.
        
    except Exception as e:
        print(f"업데이트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db_manager.disconnect()
        print("=== 작업 종료 ===")

if __name__ == "__main__":
    update_top_stocks()
