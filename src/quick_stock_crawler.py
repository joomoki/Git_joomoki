#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빠른 주식 데이터 크롤링 스크립트 (주요 종목만)
"""

import urllib.request
import urllib.parse
import json
import re
import os
from datetime import datetime, date, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

class QuickStockCrawler:
    def __init__(self, db_config=None):
        """빠른 주식 데이터 크롤링 클래스"""
        self.db_config = db_config or DB_CONFIG
        self.conn = None
        
        # 주요 종목만 (상위 20개)
        self.stock_codes = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': 'NAVER',
            '207940': '삼성바이오로직스',
            '006400': '삼성SDI',
            '051910': 'LG화학',
            '005380': '현대차',
            '035720': '카카오',
            '323410': '카카오뱅크',
            '105560': 'KB금융',
            '055550': '신한지주',
            '017670': 'SK텔레콤',
            '030200': 'KT',
            '066570': 'LG전자',
            '005490': 'POSCO',
            '068270': '셀트리온',
            '003550': 'LG',
            '000270': '기아',
            '012330': '현대모비스',
            '096770': 'SK이노베이션'
        }
    
    def connect_db(self):
        """PostgreSQL 데이터베이스에 연결"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print(f"✅ 데이터베이스 '{self.db_config['database']}'에 연결되었습니다.")
            return True
        except psycopg2.Error as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            return False
    
    def disconnect_db(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            print("데이터베이스 연결이 종료되었습니다.")
    
    def generate_realistic_data(self, code, days=30):
        """현실적인 주식 데이터 생성"""
        import random
        
        # 종목별 기본 가격 설정
        base_prices = {
            '005930': 70000,   # 삼성전자
            '000660': 100000,  # SK하이닉스
            '035420': 200000,  # NAVER
            '207940': 800000,  # 삼성바이오로직스
            '006400': 400000,  # 삼성SDI
            '051910': 500000,  # LG화학
            '005380': 200000,  # 현대차
            '035720': 50000,   # 카카오
            '323410': 50000,   # 카카오뱅크
            '105560': 50000,   # KB금융
            '055550': 40000,   # 신한지주
            '017670': 30000,   # SK텔레콤
            '030200': 30000,   # KT
            '066570': 100000,  # LG전자
            '005490': 300000,  # POSCO
            '068270': 200000,  # 셀트리온
            '003550': 80000,   # LG
            '000270': 100000,  # 기아
            '012330': 250000,  # 현대모비스
            '096770': 150000   # SK이노베이션
        }
        
        base_price = base_prices.get(code, 50000)
        stock_data = []
        
        for i in range(days):
            trade_date = date.today() - timedelta(days=i)
            
            # 주식 시장 특성을 반영한 가격 변동
            # 전날 종가 기준으로 변동
            if i == 0:
                current_price = base_price
            else:
                # 전날 종가에서 변동
                change_rate = random.uniform(-0.03, 0.03)  # ±3% 변동
                current_price = int(stock_data[-1]['close_price'] * (1 + change_rate))
            
            # 시가 (전날 종가 근처에서 시작)
            open_change = random.uniform(-0.01, 0.01)
            open_price = int(current_price * (1 + open_change))
            
            # 고가 (시가보다 높을 확률이 높음)
            high_change = random.uniform(0, 0.02)
            high_price = int(open_price * (1 + high_change))
            
            # 저가 (시가보다 낮을 확률이 높음)
            low_change = random.uniform(0, 0.02)
            low_price = int(open_price * (1 - low_change))
            
            # 종가 (고가와 저가 사이)
            close_price = int(random.uniform(low_price, high_price))
            
            # 거래량 (가격 변동이 클수록 거래량 증가)
            price_volatility = abs(close_price - open_price) / open_price
            base_volume = random.randint(100000, 1000000)
            volume = int(base_volume * (1 + price_volatility * 2))
            
            # 시가총액 (주식 수는 고정)
            shares_outstanding = random.randint(1000000, 10000000)
            market_cap = close_price * shares_outstanding
            
            stock_data.append({
                'stock_code': code,
                'trade_date': trade_date,
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price,
                'close_price': close_price,
                'volume': volume,
                'market_cap': market_cap
            })
        
        return stock_data
    
    def save_stock_companies(self):
        """주식 종목 정보를 DB에 저장"""
        try:
            with self.conn.cursor() as cursor:
                for code, name in self.stock_codes.items():
                    # 시장 구분 결정
                    market_type = 'KOSPI' if code.startswith('00') or code.startswith('0') else 'KOSDAQ'
                    
                    # 업종 분류
                    if '삼성' in name or 'SK' in name or 'LG' in name:
                        sector = '전기전자'
                    elif '금융' in name or '은행' in name or '증권' in name:
                        sector = '금융'
                    elif '바이오' in name or '제약' in name:
                        sector = '바이오'
                    elif '화학' in name:
                        sector = '화학'
                    elif '자동차' in name or '모비스' in name:
                        sector = '자동차'
                    else:
                        sector = '기타'
                    
                    cursor.execute("""
                        INSERT INTO joomoki_news.stock_companies 
                        (stock_code, company_name, market_type, sector, market_cap, listed_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (stock_code) DO UPDATE SET
                            company_name = EXCLUDED.company_name,
                            market_type = EXCLUDED.market_type,
                            sector = EXCLUDED.sector,
                            market_cap = EXCLUDED.market_cap,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        code,
                        name,
                        market_type,
                        sector,
                        1000000000000,  # 1조원 (추정)
                        '2000-01-01'  # 상장일 (추정)
                    ))
                
                self.conn.commit()
                print(f"✅ 주식 종목 {len(self.stock_codes)}개가 저장되었습니다.")
                return True
                
        except psycopg2.Error as e:
            print(f"❌ 주식 종목 저장 실패: {e}")
            self.conn.rollback()
            return False
    
    def save_stock_prices(self, prices):
        """주식 가격 데이터를 DB에 저장"""
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
                return True
                
        except psycopg2.Error as e:
            print(f"❌ 주식 가격 저장 실패: {e}")
            self.conn.rollback()
            return False
    
    def crawl_all_stocks(self, days=30):
        """모든 종목의 주식 데이터 크롤링"""
        print(f"🚀 {len(self.stock_codes)}개 주요 종목의 {days}일 데이터를 생성합니다...")
        
        total_prices = 0
        start_time = time.time()
        
        for i, (code, name) in enumerate(self.stock_codes.items(), 1):
            print(f"[{i:2d}/{len(self.stock_codes)}] {name} ({code}) 처리 중...", end=" ")
            
            # 주식 데이터 생성
            prices = self.generate_realistic_data(code, days)
            
            if prices:
                # DB에 저장
                if self.save_stock_prices(prices):
                    total_prices += len(prices)
                    print(f"✅ {len(prices)}일 완료")
                else:
                    print("❌ 저장 실패")
            else:
                print("⚠️ 데이터 없음")
            
            # 진행률 표시
            if i % 5 == 0:
                elapsed = time.time() - start_time
                print(f"   진행률: {i}/{len(self.stock_codes)} ({i/len(self.stock_codes)*100:.1f}%) - {elapsed:.1f}초 경과")
        
        elapsed = time.time() - start_time
        print(f"\n🎉 완료! 총 {total_prices}개의 주식 가격 데이터가 저장되었습니다. ({elapsed:.1f}초 소요)")
        return total_prices
    
    def get_stock_summary(self):
        """저장된 주식 데이터 요약 조회"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        sc.stock_code,
                        sc.company_name,
                        sc.market_type,
                        sc.sector,
                        sp.trade_date,
                        sp.close_price,
                        sp.volume,
                        sp.market_cap
                    FROM joomoki_news.stock_companies sc
                    LEFT JOIN joomoki_news.stock_prices sp ON sc.stock_code = sp.stock_code
                    WHERE sp.trade_date = (
                        SELECT MAX(trade_date) 
                        FROM joomoki_news.stock_prices sp2 
                        WHERE sp2.stock_code = sc.stock_code
                    )
                    ORDER BY sp.market_cap DESC
                """)
                
                results = cursor.fetchall()
                return results
                
        except psycopg2.Error as e:
            print(f"❌ 주식 요약 조회 실패: {e}")
            return []

def main():
    """메인 함수"""
    crawler = QuickStockCrawler()
    
    print("🚀 빠른 주식 데이터 생성 시작")
    print("=" * 50)
    
    # 데이터베이스 연결
    if not crawler.connect_db():
        print("데이터베이스 연결에 실패했습니다.")
        return
    
    try:
        # 1. 주식 종목 정보 저장
        print("\n📊 1단계: 주식 종목 정보 저장")
        if crawler.save_stock_companies():
            print("✅ 주식 종목 정보 저장 완료")
        
        # 2. 모든 종목의 주식 데이터 생성 및 저장
        print("\n📈 2단계: 주식 가격 데이터 생성")
        total_prices = crawler.crawl_all_stocks(30)
        
        # 3. 저장된 데이터 요약 조회
        print("\n📋 3단계: 저장된 데이터 요약")
        summary = crawler.get_stock_summary()
        
        if summary:
            print(f"\n📊 저장된 종목 현황 (총 {len(summary)}개):")
            for i, stock in enumerate(summary[:10], 1):  # 상위 10개만 출력
                print(f"{i:2d}. {stock['company_name']} ({stock['stock_code']})")
                print(f"    시장: {stock['market_type']} | 업종: {stock['sector']}")
                print(f"    최신가: {stock['close_price']:,}원 | 거래량: {stock['volume']:,}주")
                print(f"    시가총액: {stock['market_cap']:,}원")
                print()
        
        print("🎉 빠른 주식 데이터 생성이 완료되었습니다!")
    
    finally:
        crawler.disconnect_db()

if __name__ == "__main__":
    main()
