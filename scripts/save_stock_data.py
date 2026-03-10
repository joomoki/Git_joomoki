import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kis_client import KisApiClient
from src.stock_db_manager import StockDBManager

def save_samsung_electronics_data():
    print("=== 삼성전자 주가 데이터 수집 및 저장 시작 ===")
    
    # 1. API 클라이언트 및 DB 매니저 초기화
    api_client = KisApiClient()
    db_manager = StockDBManager()
    
    if not db_manager.connect():
        print("DB 연결 실패로 중단합니다.")
        return

    try:
        stock_code = "005930" # 삼성전자
        company_name = "삼성전자"
        
        # 2. 토큰 발급 (필요시)
        api_client.get_access_token()

        # 3. 종목 기본 정보 저장 (임시 데이터)
        # 실제로는 별도 API로 상세 정보를 가져와야 하지만, 우선 기본 정보만 저장
        company_info = {
            'stock_code': stock_code,
            'company_name': company_name,
            'market_type': 'KOSPI', # 예시
            # 'sector': '전기전자',
        }
        print(f"종목 정보 저장: {company_name} ({stock_code})")
        db_manager.insert_stock_company(company_info)

        # 4. 일별 주가 데이터 조회 (최근 30일 -> API 로직에 따라 다름, get_historical_price 사용 권장)
        # get_daily_price는 최근 30일치(output 리스트)를 주진 않고 현재가 정보 위주이거나,
        # API 문서에 따라 output 배열이 일별 데이터일 수 있음.
        # kis_client.py의 get_daily_price 구현을 보면 output을 반환함. 
        # 국내주식현재가 일자별(FHKST01010400) API 응답 output은 일자별 데이터를 리스트로 줌.
        
        print(f"일별 시세 데이터 조회 중...")
        daily_prices = api_client.get_daily_price(stock_code)
        
        if daily_prices:
            print(f"수신된 데이터: {len(daily_prices)}건")
            # 5. DB 저장
            db_manager.insert_daily_prices(stock_code, daily_prices)
        else:
            print("데이터 수신 실패")

    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_manager.disconnect()
        print("=== 작업 종료 ===")

if __name__ == "__main__":
    save_samsung_electronics_data()
