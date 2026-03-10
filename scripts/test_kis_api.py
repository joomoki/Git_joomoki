import sys
import os
import pprint

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kis_client import KisApiClient

def test_kis_api():
    print("=== KIS API 연동 테스트 시작 ===")
    
    try:
        client = KisApiClient()
        
        # 1. 토큰 발급 테스트
        print("\n[1] 토큰 발급 요청 중...")
        token = client.get_access_token()
        if token:
            print(f"성공: 토큰 발급 완료 (앞 10자리: {token[:10]}...)")
        else:
            print("실패: 토큰을 받아오지 못했습니다.")
            return

        # 2. 주식 현재가 조회 테스트 (삼성전자: 005930)
        stock_code = "005930"
        print(f"\n[2] {stock_code} (삼성전자) 일별 시세 조회 요청 중...")
        daily_price = client.get_daily_price(stock_code)
        
        if daily_price:
            print(f"성공: {len(daily_price)}일치 데이터를 가져왔습니다.")
            print("최근 1일 데이터:")
            pprint.pprint(daily_price[0])
        else:
            print("실패: 데이터를 가져오지 못했습니다.")

    except Exception as e:
        print(f"\n에러 발생: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== KIS API 연동 테스트 종료 ===")

if __name__ == "__main__":
    test_kis_api()
