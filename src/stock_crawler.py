#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
주식 데이터 크롤링 스크립트
"""

import urllib.request
import urllib.parse
import json
import re
import os
from datetime import datetime, date
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

class StockCrawler:
    def __init__(self, db_config=None):
        """주식 데이터 크롤링 클래스"""
        self.db_config = db_config or DB_CONFIG
        self.conn = None
    
    def connect_db(self):
        """PostgreSQL 데이터베이스에 연결"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print(f"데이터베이스 '{self.db_config['database']}'에 연결되었습니다.")
            return True
        except psycopg2.Error as e:
            print(f"데이터베이스 연결 실패: {e}")
            return False
    
    def disconnect_db(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            print("데이터베이스 연결이 종료되었습니다.")
    
    def crawl_stock_list(self):
        """주식 종목 리스트 크롤링 (예시: KRX에서)"""
        # 실제로는 KRX API나 금융 데이터 제공업체 API를 사용해야 함
        # 여기서는 샘플 데이터를 생성
        sample_stocks = [
            {
                'stock_code': '005930',
                'company_name': '삼성전자',
                'market_type': 'KOSPI',
                'sector': '전기전자',
                'market_cap': 400000000000000,  # 400조원
                'listed_date': '1975-06-11'
            },
            {
                'stock_code': '000660',
                'company_name': 'SK하이닉스',
                'market_type': 'KOSPI',
                'sector': '전기전자',
                'market_cap': 80000000000000,   # 80조원
                'listed_date': '1996-10-01'
            },
            {
                'stock_code': '035420',
                'company_name': 'NAVER',
                'market_type': 'KOSPI',
                'sector': '서비스업',
                'market_cap': 30000000000000,   # 30조원
                'listed_date': '2008-10-15'
            },
            {
                'stock_code': '207940',
                'company_name': '삼성바이오로직스',
                'market_type': 'KOSPI',
                'sector': '의료정밀',
                'market_cap': 150000000000000,  # 150조원
                'listed_date': '2016-11-10'
            },
            {
                'stock_code': '006400',
                'company_name': '삼성SDI',
                'market_type': 'KOSPI',
                'sector': '전기전자',
                'market_cap': 50000000000000,   # 50조원
                'listed_date': '1999-07-22'
            }
        ]
        
        return sample_stocks
    
    def crawl_stock_price(self, stock_code, days=30):
        """주식 가격 데이터 크롤링 (최근 N일)"""
        # 실제로는 금융 데이터 API를 사용해야 함
        # 여기서는 샘플 데이터를 생성
        import random
        from datetime import timedelta
        
        base_price = 70000 if stock_code == '005930' else 100000  # 삼성전자 기준
        prices = []
        
        for i in range(days):
            trade_date = date.today() - timedelta(days=i)
            
            # 가격 변동 시뮬레이션
            change_rate = random.uniform(-0.05, 0.05)  # ±5% 변동
            open_price = base_price * (1 + change_rate)
            high_price = open_price * (1 + random.uniform(0, 0.03))
            low_price = open_price * (1 - random.uniform(0, 0.03))
            close_price = open_price * (1 + random.uniform(-0.02, 0.02))
            volume = random.randint(1000000, 10000000)
            
            prices.append({
                'stock_code': stock_code,
                'trade_date': trade_date,
                'open_price': round(open_price, 2),
                'high_price': round(high_price, 2),
                'low_price': round(low_price, 2),
                'close_price': round(close_price, 2),
                'volume': volume,
                'market_cap': base_price * 1000000000  # 시가총액 추정
            })
            
            base_price = close_price  # 다음날 기준가격
        
        return prices
    
    def save_stock_companies(self, companies):
        """주식 종목 정보 저장"""
        try:
            with self.conn.cursor() as cursor:
                for company in companies:
                    cursor.execute("""
                        INSERT INTO joomoki_news.stock_companies 
                        (stock_code, company_name, market_type, sector, market_cap, listed_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (stock_code) DO UPDATE SET
                            company_name = EXCLUDED.company_name,
                            market_type = EXCLUDED.market_type,
                            sector = EXCLUDED.sector,
                            market_cap = EXCLUDED.market_cap,
                            listed_date = EXCLUDED.listed_date,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        company['stock_code'],
                        company['company_name'],
                        company['market_type'],
                        company['sector'],
                        company['market_cap'],
                        company['listed_date']
                    ))
                
                self.conn.commit()
                print(f"주식 종목 {len(companies)}개가 저장되었습니다.")
                return True
                
        except psycopg2.Error as e:
            print(f"주식 종목 저장 실패: {e}")
            self.conn.rollback()
            return False
    
    def save_stock_prices(self, prices):
        """주식 가격 데이터 저장"""
        try:
            with self.conn.cursor() as cursor:
                for price in prices:
                    cursor.execute("""
                        INSERT INTO joomoki_news.stock_prices 
                        (stock_code, trade_date, open_price, high_price, low_price, close_price, volume, market_cap)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                            open_price = EXCLUDED.open_price,
                            high_price = EXCLUDED.high_price,
                            low_price = EXCLUDED.low_price,
                            close_price = EXCLUDED.close_price,
                            volume = EXCLUDED.volume,
                            market_cap = EXCLUDED.market_cap
                    """, (
                        price['stock_code'],
                        price['trade_date'],
                        price['open_price'],
                        price['high_price'],
                        price['low_price'],
                        price['close_price'],
                        price['volume'],
                        price['market_cap']
                    ))
                
                self.conn.commit()
                print(f"주식 가격 데이터 {len(prices)}개가 저장되었습니다.")
                return True
                
        except psycopg2.Error as e:
            print(f"주식 가격 저장 실패: {e}")
            self.conn.rollback()
            return False
    
    def get_stock_companies(self):
        """저장된 주식 종목 목록 조회"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT stock_code, company_name, market_type, sector, market_cap
                    FROM joomoki_news.stock_companies
                    ORDER BY market_cap DESC
                """)
                companies = cursor.fetchall()
                return companies
        except psycopg2.Error as e:
            print(f"주식 종목 조회 실패: {e}")
            return []
    
    def get_stock_prices(self, stock_code, days=30):
        """특정 종목의 가격 데이터 조회"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT trade_date, open_price, high_price, low_price, close_price, volume
                    FROM joomoki_news.stock_prices
                    WHERE stock_code = %s
                    ORDER BY trade_date DESC
                    LIMIT %s
                """, (stock_code, days))
                prices = cursor.fetchall()
                return prices
        except psycopg2.Error as e:
            print(f"주식 가격 조회 실패: {e}")
            return []

def main():
    """메인 함수"""
    crawler = StockCrawler()
    
    print("주식 데이터 크롤링 시작...")
    
    # 데이터베이스 연결
    if not crawler.connect_db():
        print("데이터베이스 연결에 실패했습니다.")
        return
    
    try:
        # 1. 주식 종목 리스트 크롤링 및 저장
        print("\n=== 주식 종목 리스트 크롤링 ===")
        companies = crawler.crawl_stock_list()
        if crawler.save_stock_companies(companies):
            print("주식 종목 정보가 저장되었습니다.")
        
        # 2. 각 종목의 가격 데이터 크롤링 및 저장
        print("\n=== 주식 가격 데이터 크롤링 ===")
        for company in companies:
            stock_code = company['stock_code']
            company_name = company['company_name']
            print(f"크롤링 중: {company_name} ({stock_code})")
            
            prices = crawler.crawl_stock_price(stock_code, 30)
            if crawler.save_stock_prices(prices):
                print(f"  - {company_name} 가격 데이터 저장 완료")
        
        # 3. 저장된 데이터 확인
        print("\n=== 저장된 데이터 확인 ===")
        saved_companies = crawler.get_stock_companies()
        print(f"저장된 종목 수: {len(saved_companies)}")
        
        for company in saved_companies[:3]:  # 상위 3개만 출력
            print(f"- {company['company_name']} ({company['stock_code']}) - {company['market_type']}")
            
            # 최근 가격 데이터 조회
            recent_prices = crawler.get_stock_prices(company['stock_code'], 5)
            if recent_prices:
                latest = recent_prices[0]
                print(f"  최근 종가: {latest['close_price']:,}원 (거래량: {latest['volume']:,})")
    
    finally:
        crawler.disconnect_db()

if __name__ == "__main__":
    main()
