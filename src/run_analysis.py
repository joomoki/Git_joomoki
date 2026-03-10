#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
뉴스-주식 분석 실행 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crawler_with_db import DaumNewsCrawlerWithDB
from src.stock_crawler import StockCrawler
from src.news_stock_analyzer import NewsStockAnalyzer
from config.db_config import DB_CONFIG

def run_full_analysis():
    """전체 분석 프로세스 실행"""
    print("🚀 뉴스-주식 분석 시스템 시작")
    print("=" * 50)
    
    # 1. 뉴스 크롤링
    print("\n📰 1단계: 뉴스 크롤링")
    news_crawler = DaumNewsCrawlerWithDB()
    
    if news_crawler.connect_db():
        # 샘플 뉴스 URL들 (실제로는 여러 뉴스 사이트에서 수집)
        news_urls = [
            "https://v.daum.net/v/20250927201941985",  # 기존 URL
            # 추가 뉴스 URL들을 여기에 추가
        ]
        
        for url in news_urls:
            print(f"크롤링 중: {url}")
            article_data = news_crawler.crawl_article(url)
            if article_data:
                news_crawler.save_to_database(article_data)
        
        news_crawler.disconnect_db()
        print("✅ 뉴스 크롤링 완료")
    
    # 2. 주식 데이터 크롤링
    print("\n📈 2단계: 주식 데이터 크롤링")
    stock_crawler = StockCrawler()
    
    if stock_crawler.connect_db():
        # 주식 종목 리스트 크롤링
        companies = stock_crawler.crawl_stock_list()
        stock_crawler.save_stock_companies(companies)
        
        # 각 종목의 가격 데이터 크롤링
        for company in companies:
            prices = stock_crawler.crawl_stock_price(company['stock_code'], 30)
            stock_crawler.save_stock_prices(prices)
        
        stock_crawler.disconnect_db()
        print("✅ 주식 데이터 크롤링 완료")
    
    # 3. 뉴스-주식 분석
    print("\n🔍 3단계: 뉴스-주식 분석")
    analyzer = NewsStockAnalyzer()
    
    if analyzer.connect_db():
        # 뉴스 기사 분석
        analyzer.analyze_news_articles()
        
        # 각 종목별 분석 결과 생성
        stock_codes = ['005930', '000660', '035420', '207940', '006400']
        for stock_code in stock_codes:
            analyzer.generate_stock_analysis(stock_code)
        
        # 분석 결과 출력
        print("\n📊 분석 결과:")
        results = analyzer.get_analysis_results(5)
        
        for result in results:
            print(f"\n🏢 {result['company_name']} ({result['stock_code']})")
            print(f"   📈 뉴스 영향도: {result['news_impact_score']:.2f}")
            print(f"   😊 감정 트렌드: {result['sentiment_trend']}")
            print(f"   📊 가격 예측: {result['price_prediction']}")
            print(f"   🎯 신뢰도: {result['confidence_level']:.2f}")
        
        analyzer.disconnect_db()
        print("✅ 뉴스-주식 분석 완료")
    
    print("\n🎉 전체 분석 프로세스가 완료되었습니다!")

def run_news_only():
    """뉴스 크롤링만 실행"""
    print("📰 뉴스 크롤링 실행")
    
    news_crawler = DaumNewsCrawlerWithDB()
    
    if news_crawler.connect_db():
        url = "https://v.daum.net/v/20250927201941985"
        article_data = news_crawler.crawl_article(url)
        
        if article_data:
            news_crawler.save_to_database(article_data)
            print("✅ 뉴스 크롤링 완료")
        
        news_crawler.disconnect_db()

def run_stock_only():
    """주식 데이터 크롤링만 실행"""
    print("📈 주식 데이터 크롤링 실행")
    
    stock_crawler = StockCrawler()
    
    if stock_crawler.connect_db():
        companies = stock_crawler.crawl_stock_list()
        stock_crawler.save_stock_companies(companies)
        
        for company in companies:
            prices = stock_crawler.crawl_stock_price(company['stock_code'], 30)
            stock_crawler.save_stock_prices(prices)
        
        print("✅ 주식 데이터 크롤링 완료")
        stock_crawler.disconnect_db()

def run_analysis_only():
    """분석만 실행"""
    print("🔍 뉴스-주식 분석 실행")
    
    analyzer = NewsStockAnalyzer()
    
    if analyzer.connect_db():
        analyzer.analyze_news_articles()
        
        stock_codes = ['005930', '000660', '035420', '207940', '006400']
        for stock_code in stock_codes:
            analyzer.generate_stock_analysis(stock_code)
        
        results = analyzer.get_analysis_results(5)
        
        print("\n📊 분석 결과:")
        for result in results:
            print(f"\n🏢 {result['company_name']} ({result['stock_code']})")
            print(f"   📈 뉴스 영향도: {result['news_impact_score']:.2f}")
            print(f"   😊 감정 트렌드: {result['sentiment_trend']}")
            print(f"   📊 가격 예측: {result['price_prediction']}")
            print(f"   🎯 신뢰도: {result['confidence_level']:.2f}")
        
        analyzer.disconnect_db()
        print("✅ 분석 완료")

def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "news":
            run_news_only()
        elif mode == "stock":
            run_stock_only()
        elif mode == "analysis":
            run_analysis_only()
        elif mode == "full":
            run_full_analysis()
        else:
            print("사용법: python run_analysis.py [news|stock|analysis|full]")
    else:
        print("뉴스-주식 분석 시스템")
        print("사용법:")
        print("  python run_analysis.py news     - 뉴스 크롤링만")
        print("  python run_analysis.py stock    - 주식 데이터 크롤링만")
        print("  python run_analysis.py analysis - 분석만")
        print("  python run_analysis.py full     - 전체 프로세스")

if __name__ == "__main__":
    main()
