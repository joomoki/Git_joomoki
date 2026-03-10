import sys
import os
import time
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kis_client import KisApiClient
from src.stock_db_manager import StockDBManager

def update_all_stocks():
    print("=== 전 종목 데이터 일괄 업데이트 시작 ===")
    
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

        # 2. DB에 저장된 모든 종목 가져오기
        all_stocks = db_manager.get_all_stocks()
        total_count = len(all_stocks)
        print(f"업데이트 대상 종목: {total_count}개")
        
        if total_count == 0:
            print("DB에 종목이 없습니다. scripts/download_master.py를 먼저 실행해주세요.")
            return

        # 3. 순차적으로 데이터 수집
        success_count = 0
        fail_count = 0
        
        for i, stock in enumerate(all_stocks):
            stock_code = stock[0]
            market_type = stock[1]
            company_name = stock[2]
            
            print(f"[{i+1}/{total_count}] {company_name}({stock_code}) 업데이트 중...", end='\r')
            
            try:
                # (1) 일별 시세 (최근 30일)
                daily_prices = api_client.get_daily_price(stock_code)
                if daily_prices:
                    db_manager.insert_daily_prices(stock_code, daily_prices)
                
                # (2) 상세 재무/기본 정보 (현재가 상세)
                # PER, PBR, 매출액 등 (확장된 insert_daily_fundamentals 사용)
                detailed_info = api_client.get_current_price_detailed(stock_code)
                if detailed_info:
                    db_manager.save_daily_fundamentals(stock_code, detailed_info)
                    
                # (3) 투자자별 매매동향 (외국인/기관)
                investor_trend = api_client.get_investor_trend(stock_code)
                if investor_trend:
                    db_manager.insert_investor_trend(stock_code, investor_trend)
                
                success_count += 1
                
                # API 호출 제한 고려 (안전하게 0.2초 대기 - 3번 호출하므로)
                time.sleep(0.2)
                
            except Exception as e:
                print(f"\n  -> {company_name} 업데이트 실패: {e}")
                fail_count += 1
                
            # 100개마다 진행상황 로그 출력
            if (i+1) % 100 == 0:
                print(f"\n[진행중] 완료: {i+1}, 성공: {success_count}, 실패: {fail_count}")

        print(f"\n=== 전체 업데이트 완료 ===")
        print(f"총 종목: {total_count}")
        print(f"성공: {success_count}")
        print(f"실패: {fail_count}")
        
    except Exception as e:
        print(f"업데이트 중 치명적 오류: {e}")
    finally:
        db_manager.disconnect()

if __name__ == "__main__":
    update_all_stocks()
