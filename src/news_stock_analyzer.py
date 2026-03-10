#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
뉴스-주식 분석 도구
"""

import re
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

class NewsStockAnalyzer:
    def __init__(self, db_config=None):
        """뉴스-주식 분석 클래스"""
        self.db_config = db_config or DB_CONFIG
        self.conn = None
        
        # 주식 관련 키워드 매핑
        self.stock_keywords = {
            '삼성전자': '005930',
            '삼성': '005930',
            'SK하이닉스': '000660',
            '하이닉스': '000660',
            'NAVER': '035420',
            '네이버': '035420',
            '삼성바이오로직스': '207940',
            '삼성바이오': '207940',
            '삼성SDI': '006400',
            'SDI': '006400',
            'LG화학': '051910',
            'LG': '051910',
            '현대차': '005380',
            '현대': '005380',
            '카카오': '035720',
            '카카오뱅크': '323410',
            'KB금융': '105560',
            '신한지주': '055550',
            '하나금융': '086790',
            'SK텔레콤': '017670',
            'KT': '030200',
            'LG전자': '066570',
            'POSCO': '005490',
            '포스코': '005490'
        }
        
        # 감정 분석 키워드
        self.positive_keywords = [
            '상승', '급등', '호재', '긍정', '성장', '확대', '증가', '개선', '회복',
            '투자', '계약', '수주', '실적', '이익', '매출', '영업이익', '순이익',
            '혁신', '기술', '개발', '신제품', '출시', '진출', '확장', '투자유치'
        ]
        
        self.negative_keywords = [
            '하락', '급락', '악재', '부정', '감소', '축소', '악화', '손실', '적자',
            '실적부진', '매출감소', '영업손실', '순손실', '부채', '경영위기',
            '규제', '제재', '소송', '분쟁', '사고', '문제', '위험', '불안'
        ]
    
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
    
    def extract_stock_keywords(self, text):
        """텍스트에서 주식 관련 키워드 추출"""
        found_stocks = {}
        
        for keyword, stock_code in self.stock_keywords.items():
            if keyword in text:
                # 키워드가 나타난 횟수 계산
                count = text.count(keyword)
                found_stocks[stock_code] = {
                    'keyword': keyword,
                    'frequency': count,
                    'relevance_score': min(count * 0.1, 1.0)  # 최대 1.0
                }
        
        return found_stocks
    
    def analyze_sentiment(self, text):
        """텍스트 감정 분석"""
        positive_count = sum(1 for word in self.positive_keywords if word in text)
        negative_count = sum(1 for word in self.negative_keywords if word in text)
        
        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            return 0.0  # 중립
        
        sentiment_score = (positive_count - negative_count) / total_keywords
        return max(-1.0, min(1.0, sentiment_score))  # -1.0 ~ 1.0 범위로 제한
    
    def analyze_news_articles(self):
        """뉴스 기사들을 분석하여 주식과 연결"""
        try:
            with self.conn.cursor() as cursor:
                # 최근 뉴스 기사들 조회
                cursor.execute("""
                    SELECT id, title, content, category, crawled_at
                    FROM joomoki_news.news_articles
                    WHERE crawled_at >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY crawled_at DESC
                """)
                
                articles = cursor.fetchall()
                print(f"분석할 뉴스 기사 수: {len(articles)}")
                
                for article in articles:
                    article_id, title, content, category, crawled_at = article
                    
                    # 제목과 본문을 합쳐서 분석
                    full_text = f"{title} {content}"
                    
                    # 주식 키워드 추출
                    stock_keywords = self.extract_stock_keywords(full_text)
                    
                    if stock_keywords:
                        print(f"\n기사 ID {article_id}: {title[:50]}...")
                        
                        # 감정 분석
                        sentiment_score = self.analyze_sentiment(full_text)
                        
                        # 각 주식과의 관계 저장
                        for stock_code, info in stock_keywords.items():
                            cursor.execute("""
                                INSERT INTO joomoki_news.news_stock_relations 
                                (article_id, stock_code, relevance_score, sentiment_score)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (article_id, stock_code) DO UPDATE SET
                                    relevance_score = EXCLUDED.relevance_score,
                                    sentiment_score = EXCLUDED.sentiment_score
                            """, (article_id, stock_code, info['relevance_score'], sentiment_score))
                            
                            print(f"  - {info['keyword']} ({stock_code}): 관련도 {info['relevance_score']:.2f}, 감정 {sentiment_score:.2f}")
                            
                            # 키워드 빈도 업데이트
                            cursor.execute("""
                                INSERT INTO joomoki_news.stock_keywords 
                                (keyword, stock_code, frequency, last_mentioned)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (keyword, stock_code) DO UPDATE SET
                                    frequency = stock_keywords.frequency + 1,
                                    last_mentioned = EXCLUDED.last_mentioned
                            """, (info['keyword'], stock_code, info['frequency'], crawled_at))
                
                self.conn.commit()
                print(f"\n뉴스-주식 분석이 완료되었습니다.")
                return True
                
        except psycopg2.Error as e:
            print(f"뉴스 분석 실패: {e}")
            self.conn.rollback()
            return False
    
    def generate_stock_analysis(self, stock_code):
        """특정 종목의 분석 결과 생성"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 최근 7일간의 뉴스 영향 분석
                cursor.execute("""
                    SELECT 
                        AVG(nsr.sentiment_score) as avg_sentiment,
                        COUNT(*) as news_count,
                        AVG(nsr.relevance_score) as avg_relevance
                    FROM joomoki_news.news_stock_relations nsr
                    JOIN joomoki_news.news_articles na ON nsr.article_id = na.id
                    WHERE nsr.stock_code = %s
                    AND na.crawled_at >= CURRENT_DATE - INTERVAL '7 days'
                """, (stock_code,))
                
                analysis_data = cursor.fetchone()
                
                if analysis_data and analysis_data['news_count'] > 0:
                    avg_sentiment = float(analysis_data['avg_sentiment'])
                    news_count = analysis_data['news_count']
                    avg_relevance = float(analysis_data['avg_relevance'])
                    
                    # 뉴스 영향도 점수 계산
                    news_impact_score = avg_sentiment * avg_relevance * news_count * 10
                    
                    # 감정 트렌드 결정
                    if avg_sentiment > 0.2:
                        sentiment_trend = 'POSITIVE'
                    elif avg_sentiment < -0.2:
                        sentiment_trend = 'NEGATIVE'
                    else:
                        sentiment_trend = 'NEUTRAL'
                    
                    # 가격 예측
                    if avg_sentiment > 0.3:
                        price_prediction = 'UP'
                    elif avg_sentiment < -0.3:
                        price_prediction = 'DOWN'
                    else:
                        price_prediction = 'HOLD'
                    
                    # 신뢰도 계산
                    confidence_level = min(avg_relevance * news_count / 10, 1.0)
                    
                    # 분석 요약 생성
                    analysis_summary = f"""
                    최근 7일간 {news_count}건의 뉴스에서 언급되었습니다.
                    평균 감정 점수: {avg_sentiment:.2f}
                    평균 관련도: {avg_relevance:.2f}
                    뉴스 영향도: {news_impact_score:.2f}
                    """
                    
                    # 분석 결과 저장
                    cursor.execute("""
                        INSERT INTO joomoki_news.stock_analysis 
                        (stock_code, analysis_date, news_impact_score, sentiment_trend, 
                         price_prediction, confidence_level, analysis_summary)
                        VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, %s)
                        ON CONFLICT (stock_code, analysis_date) DO UPDATE SET
                            news_impact_score = EXCLUDED.news_impact_score,
                            sentiment_trend = EXCLUDED.sentiment_trend,
                            price_prediction = EXCLUDED.price_prediction,
                            confidence_level = EXCLUDED.confidence_level,
                            analysis_summary = EXCLUDED.analysis_summary
                    """, (stock_code, news_impact_score, sentiment_trend, 
                          price_prediction, confidence_level, analysis_summary))
                    
                    self.conn.commit()
                    
                    return {
                        'stock_code': stock_code,
                        'news_impact_score': news_impact_score,
                        'sentiment_trend': sentiment_trend,
                        'price_prediction': price_prediction,
                        'confidence_level': confidence_level,
                        'news_count': news_count
                    }
                
                return None
                
        except psycopg2.Error as e:
            print(f"주식 분석 실패: {e}")
            return None
    
    def get_analysis_results(self, limit=10):
        """분석 결과 조회"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        sa.stock_code,
                        sc.company_name,
                        sa.news_impact_score,
                        sa.sentiment_trend,
                        sa.price_prediction,
                        sa.confidence_level,
                        sa.analysis_summary,
                        sa.analysis_date
                    FROM joomoki_news.stock_analysis sa
                    JOIN joomoki_news.stock_companies sc ON sa.stock_code = sc.stock_code
                    ORDER BY sa.news_impact_score DESC
                    LIMIT %s
                """, (limit,))
                
                results = cursor.fetchall()
                return results
                
        except psycopg2.Error as e:
            print(f"분석 결과 조회 실패: {e}")
            return []

def main():
    """메인 함수"""
    analyzer = NewsStockAnalyzer()
    
    print("뉴스-주식 분석 시작...")
    
    # 데이터베이스 연결
    if not analyzer.connect_db():
        print("데이터베이스 연결에 실패했습니다.")
        return
    
    try:
        # 1. 뉴스 기사 분석
        print("\n=== 뉴스 기사 분석 ===")
        if analyzer.analyze_news_articles():
            print("뉴스 분석이 완료되었습니다.")
        
        # 2. 각 종목별 분석 결과 생성
        print("\n=== 종목별 분석 결과 생성 ===")
        stock_codes = ['005930', '000660', '035420', '207940', '006400']
        
        for stock_code in stock_codes:
            result = analyzer.generate_stock_analysis(stock_code)
            if result:
                print(f"{stock_code}: {result['sentiment_trend']} - {result['price_prediction']} (신뢰도: {result['confidence_level']:.2f})")
        
        # 3. 분석 결과 조회 및 출력
        print("\n=== 분석 결과 요약 ===")
        results = analyzer.get_analysis_results(5)
        
        for result in results:
            print(f"\n{result['company_name']} ({result['stock_code']})")
            print(f"  뉴스 영향도: {result['news_impact_score']:.2f}")
            print(f"  감정 트렌드: {result['sentiment_trend']}")
            print(f"  가격 예측: {result['price_prediction']}")
            print(f"  신뢰도: {result['confidence_level']:.2f}")
    
    finally:
        analyzer.disconnect_db()

if __name__ == "__main__":
    main()
