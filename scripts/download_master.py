import requests
import re
import sys
import os
import time

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager

def crawl_naver_finance(sosok_code):
    """
    네이버 금융 시가총액 페이지 크롤링
    sosok_code: 0(코스피), 1(코스닥)
    """
    stocks = []
    page = 1
    
    # 정규식 패턴: <a href="/item/main.naver?code=005930" class="tltle">삼성전자</a>
    pattern = re.compile(r'<a href="/item/main.naver\?code=(\d{6})" class="tltle">(.+?)</a>')
    
    print(f"[{'코스피' if sosok_code == 0 else '코스닥'}] 수집 시작...")
    
    while True:
        url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok_code}&page={page}"
        try:
            res = requests.get(url)
            # 인코딩 처리 (EUC-KR)
            content = res.content.decode('euc-kr', 'replace')
            
            matches = pattern.findall(content)
            if not matches:
                print(f"페이지 {page}에서 데이터 없음. 수집 종료.")
                break
                
            for code, name in matches:
                # 이미 수집된 목록에 있는지 확인 (중복 방지)
                # 네이버 페이지 특성상 마지막 페이지 이후에도 이전 내용이 나올 수 있음?
                # -> 보통 빈 테이블이 나옴. matches가 없으면 종료됨.
                # 그러나 네이버는 페이지 넘어가도 계속 마지막 페이지 보여주는 경우가 있음.
                # 따라서 이전 페이지의 마지막 종목과 같으면 종료하는 로직 필요.
                pass
            
            # 리스트에 추가
            count_before = len(stocks)
            for code, name in matches:
                # name에 HTML 엔티티 등이 있을수 있음
                name = name.replace('&amp;', '&').strip()
                stocks.append((code, name))
            
            # 중복 제거 (set 사용)
            stocks = list(set(stocks))
            
            print(f"페이지 {page} 완료 (누적 {len(stocks)}개)")
            
            # 종료 조건: 
            # 네이버 금융은 페이지가 초과되어도 마지막 페이지를 계속 보여줌.
            # 따라서 이번 페이지에서 새로 추가된 종목이 없으면 종료.
            # 하지만 set으로 처리하면 순서가 섞여서 비교 어려움.
            # matches가 이전 페이지와 동일하면 종료.
            
            if page > 100: # 안전장치 (코스피/코스닥 합쳐도 4000개 미만, 한페이지 50개 -> 최대 80페이지)
                break
                
            page += 1
            time.sleep(0.5) # 매너 딜레이
            
        except Exception as e:
            print(f"크롤링 중 오류: {e}")
            break
            
    return stocks

def update_master_data():
    db = StockDBManager()
    if not db.connect():
        print("DB 연결 실패")
        return

    # 1. 코스피 (0)
    kospi_data = crawl_naver_finance(0)
    print(f"코스피 총 {len(kospi_data)}개 종목 발견")
    
    for code, name in kospi_data:
        db.insert_stock_company({
            'stock_code': code,
            'company_name': name,
            'market_type': 'KOSPI'
        })
        
    # 2. 코스닥 (1)
    kosdaq_data = crawl_naver_finance(1)
    print(f"코스닥 총 {len(kosdaq_data)}개 종목 발견")

    for code, name in kosdaq_data:
        db.insert_stock_company({
            'stock_code': code,
            'company_name': name,
            'market_type': 'KOSDAQ'
        })

    print("전 종목 DB 업데이트 완료")
    db.disconnect()

if __name__ == "__main__":
    update_master_data()
