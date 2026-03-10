#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
삼성전자 주식 데이터 테스트 스크립트
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
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

class SamsungStockTest:
    def __init__(self, db_config=None):
        """삼성전자 주식 테스트 클래스"""
        self.db_config = db_config or DB_CONFIG
        self.conn = None
        
        # 삼성전자만
        self.stock_code = '005930'
        self.company_name = '삼성전자'
    
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
    
    def generate_samsung_data(self, days=30):
        """삼성전자 주식 데이터 생성"""
        print(f"📊 삼성전자 {days}일 주식 데이터 생성 중...")
        
        # 삼성전자 기준가격 (70,000원)
        base_price = 70000
        stock_data = []
        
        for i in range(days):
            trade_date = date.today() - timedelta(days=i)
            
            if i == 0:
                current_price = base_price
            else:
                # 전날 종가에서 변동 (주식 시장 특성 반영)
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
            
            # 거래량 (삼성전자는 대형주라 거래량 많음)
            base_volume = random.randint(5000000, 15000000)  # 500만~1500만주
            price_volatility = abs(close_price - open_price) / open_price
            volume = int(base_volume * (1 + price_volatility))
            
            # 시가총액 (삼성전자는 약 400조원)
            shares_outstanding = 5969782550  # 삼성전자 발행주식수 (실제)
            market_cap = close_price * shares_outstanding
            
            stock_data.append({
                'stock_code': self.stock_code,
                'trade_date': trade_date,
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price,
                'close_price': close_price,
                'volume': volume,
                'market_cap': market_cap
            })
        
        return stock_data
    
    def save_company_info(self):
        """삼성전자 회사 정보 저장"""
        try:
            with self.conn.cursor() as cursor:
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
                    self.stock_code,
                    self.company_name,
                    'KOSPI',
                    '전기전자',
                    400000000000000,  # 400조원
                    '1975-06-11'  # 실제 상장일
                ))
                
                self.conn.commit()
                print(f"✅ {self.company_name} 회사 정보가 저장되었습니다.")
                return True
                
        except psycopg2.Error as e:
            print(f"❌ 회사 정보 저장 실패: {e}")
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
                print(f"✅ {len(prices)}일 주식 가격 데이터가 저장되었습니다.")
                return True
                
        except psycopg2.Error as e:
            print(f"❌ 주식 가격 저장 실패: {e}")
            self.conn.rollback()
            return False
    
    def get_latest_data(self):
        """최신 주식 데이터 조회"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        sp.trade_date,
                        sp.open_price,
                        sp.high_price,
                        sp.low_price,
                        sp.close_price,
                        sp.volume,
                        sp.market_cap
                    FROM joomoki_news.stock_prices sp
                    WHERE sp.stock_code = %s
                    ORDER BY sp.trade_date DESC
                    LIMIT 10
                """, (self.stock_code,))
                
                results = cursor.fetchall()
                return results
                
        except psycopg2.Error as e:
            print(f"❌ 데이터 조회 실패: {e}")
            return []
    
    def show_price_chart(self, data):
        """가격 차트 시각화 (텍스트)"""
        if not data:
            return
        
        print(f"\n📈 {self.company_name} 최근 10일 주가 차트")
        print("=" * 60)
        print(f"{'날짜':<12} {'시가':<8} {'고가':<8} {'저가':<8} {'종가':<8} {'거래량':<12}")
        print("-" * 60)
        
        for row in data:
            print(f"{row['trade_date']} {row['open_price']:>7,} {row['high_price']:>7,} {row['low_price']:>7,} {row['close_price']:>7,} {row['volume']:>11,}")
    
    def calculate_statistics(self, data):
        """주식 통계 계산"""
        if not data:
            return
        
        prices = [row['close_price'] for row in data]
        volumes = [row['volume'] for row in data]
        
        # 기본 통계
        latest_price = prices[0]
        highest_price = max(prices)
        lowest_price = min(prices)
        avg_volume = sum(volumes) / len(volumes)
        
        # 가격 변동률
        if len(prices) > 1:
            price_change = latest_price - prices[1]
            price_change_rate = (price_change / prices[1]) * 100
        else:
            price_change = 0
            price_change_rate = 0
        
        print(f"\n📊 {self.company_name} 주식 통계")
        print("=" * 40)
        print(f"최신가: {latest_price:,}원")
        print(f"전일대비: {price_change:+,}원 ({price_change_rate:+.2f}%)")
        print(f"최고가: {highest_price:,}원")
        print(f"최저가: {lowest_price:,}원")
        print(f"평균 거래량: {avg_volume:,.0f}주")
        print(f"시가총액: {data[0]['market_cap']:,.0f}원")

def main():
    """메인 함수"""
    test = SamsungStockTest()
    
    print("🚀 삼성전자 주식 데이터 테스트 시작")
    print("=" * 50)
    
    # 데이터베이스 연결
    if not test.connect_db():
        print("데이터베이스 연결에 실패했습니다.")
        return
    
    try:
        # 1. 회사 정보 저장
        print("\n📊 1단계: 삼성전자 회사 정보 저장")
        if test.save_company_info():
            print("✅ 회사 정보 저장 완료")
        
        # 2. 주식 데이터 생성 및 저장
        print("\n📈 2단계: 주식 가격 데이터 생성")
        prices = test.generate_samsung_data(30)
        
        if test.save_stock_prices(prices):
            print("✅ 주식 가격 데이터 저장 완료")
        
        # 3. 저장된 데이터 조회 및 분석
        print("\n📋 3단계: 저장된 데이터 분석")
        latest_data = test.get_latest_data()
        
        if latest_data:
            test.show_price_chart(latest_data)
            test.calculate_statistics(latest_data)
        
        print(f"\n🎉 삼성전자 주식 데이터 테스트가 완료되었습니다!")
        print(f"   총 {len(prices)}일의 데이터가 저장되었습니다.")
    
    finally:
        test.disconnect_db()

if __name__ == "__main__":
    main()








