#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
미국 주식 데이터 수집 스크립트
"""

import sys
import os
import time
from datetime import datetime

# Force UTF-8 output for Windows console
sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kis_client import KisApiClient
from src.stock_db_manager import StockDBManager

from src.us_stock_list import US_TARGET_STOCKS
from src.us_news_collector import USNewsCollector
from src.exchange_rate import get_usd_krw_rate

# 수집 대상: us_stock_list.py에서 정의된 리스트 사용
TARGET_STOCKS = US_TARGET_STOCKS

def collect_us_data():
    print("[INFO] US Stock Data Collection Started")
    
    kis = KisApiClient()
    db = StockDBManager()
    news_collector = USNewsCollector()
    
    if not db.connect():
        print("❌ DB 연결 실패")
        return

    # 토큰 발급 확인
    if not kis.get_access_token():
        print("❌ 토큰 발급 실패")
        return

    # 1. 종목 정보 및 펀더멘털 저장
    print("\n[INFO] Step 1: Saving Company Info & Fundamentals")
    for stock in TARGET_STOCKS:
        # 해외주식 종목 상세정보 조회 (PER, EPS, 시가총액 등)
        detail = kis.get_overseas_stock_info(stock["code"], stock["market"])
        
        market_cap = None
        if detail:
            # 여기서 계산된 market_cap을 가져오고 싶지만 insert 메서드 안에서 계산함.
            # company_info 저장을 위해 market_cap을 별도로 계산
            try:
                shar = float(detail.get('shar', 0))
                last = float(detail.get('last', 0))
                if shar > 0 and last > 0:
                    market_cap = int(shar * last)
            except: pass

        company_info = {
            'stock_code': stock["code"],
            'company_name': stock["name"],
            'korean_name': stock.get("korean_name"),
            'market_type': stock["market"],
            'sector': stock["sector"],
            'market_cap': market_cap
        }
        
        if db.insert_us_stock_company(company_info):
            print(f"[SUCCESS] {stock['name']} ({stock['code']}) saved")
        else:
            print(f"[ERROR] {stock['name']} ({stock['code']}) save failed")

        if detail:
            # 펀더멘털 정보 저장
            if db.insert_us_stock_fundamentals(stock["code"], detail):
                print(f"  - Fundamentals saved for {stock['code']}")
        
        time.sleep(0.1) # API 제한 준수

    # 2. 일별 시세 저장 (2025.01.01 ~ )
    print("\n[INFO] Step 2: Saving Daily Prices (Recent 100 days)")
    # 해외주식 기간별 시세 API는 '일수'나 '기간' 기준임. 
    # 2025년 1월부터면 대략 2~3달치. 100일이면 충분.
    
    for stock in TARGET_STOCKS:
        print(f"[INFO] Collecting prices for {stock['code']}...")
        prices = kis.get_overseas_price_daily(stock["code"], days=100, market_code=stock["market"])
        
        if prices:
            # 2025년 1월 1일 이후 데이터만 필터링 및 키 매핑
            filtered_prices = []
            for p in prices:
                # API 응답: xymd(일자), clos(종가), open(시가), high(고가), low(저가), tvol(거래량)
                date_str = p.get('xymd')
                if date_str and date_str >= '20250101':
                    filtered_prices.append({
                        'date': date_str,
                        'open': float(p.get('open', 0)),
                        'high': float(p.get('high', 0)),
                        'low': float(p.get('low', 0)),
                        'close': float(p.get('clos', 0)),
                        'volume': int(p.get('tvol', 0)),
                        'adj_close': float(p.get('clos', 0)) # 수정주가 적용된 경우 clos가 수정주가임
                    })
            
            if filtered_prices:
                if db.insert_us_stock_prices(stock["code"], filtered_prices):
                    print(f"  - Saved {len(filtered_prices)} records")
                else:
                    print(f"  - DB Save Failed")
            else:
                print(f"  - No data since 2025")
        else:
            print(f"  - No API Data")
            
        time.sleep(0.1) # API 제한 준수

    # 3. 뉴스 및 감성 분석 데이터 수집
    print("\n[INFO] Step 3: Collecting News & Sentiment Analysis")
    for stock in TARGET_STOCKS:
        print(f"[INFO] Fetching news for {stock['code']} ({stock['korean_name']})...")
        news_items = news_collector.get_news(stock["code"], stock["name"], limit=5)
        
        if news_items:
            if db.insert_us_stock_news(news_items):
                print(f"  - Saved {len(news_items)} news items")
            else:
                print(f"  - DB Save Failed")
        else:
            print(f"  - No news found")
            
        time.sleep(0.5) # 구글 뉴스 크롤링 제한 방지

    # 4. 분석 결과 생성 (임시)
    print("\n[INFO] Step 4: Generating Analysis (Skipped)")
    # 환율 정보 출력 (로그 확인용)
    usd_krw = get_usd_krw_rate()
    print(f"[INFO] Current Exchange Rate: {usd_krw} KRW/USD")
    today = datetime.now().strftime('%Y-%m-%d')
    for stock in TARGET_STOCKS:
        # 최근 종가 기준 등락 파악 (Get last 2 prices)
        # DB에서 조회
        pass # 여기서는 생략하고 나중에 Analyzer에서 처리하도록 함.

    db.disconnect()
    print("\n[SUCCESS] US Stock Data Collection Completed")

if __name__ == "__main__":
    collect_us_data()
