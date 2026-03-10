#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 데이터베이스 관리 클래스
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, host='localhost', port=5432, database='news_crawler', 
                 user='postgres', password='your_password'):
        """
        PostgreSQL 데이터베이스 연결 설정
        
        Args:
            host: 데이터베이스 호스트 (기본값: localhost)
            port: 포트 번호 (기본값: 5432)
            database: 데이터베이스 이름
            user: 사용자명
            password: 비밀번호
        """
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
    
    def connect(self):
        """데이터베이스에 연결"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            print(f"데이터베이스 '{self.connection_params['database']}'에 연결되었습니다.")
            return True
        except psycopg2.Error as e:
            print(f"데이터베이스 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            print("데이터베이스 연결이 종료되었습니다.")
    
    def create_tables(self):
        """테이블 생성"""
        try:
            with self.conn.cursor() as cursor:
                # news_articles 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS news_articles (
                        id SERIAL PRIMARY KEY,
                        url VARCHAR(500) UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT,
                        author VARCHAR(100),
                        publish_date VARCHAR(50),
                        category VARCHAR(50),
                        summary TEXT,
                        crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # related_links 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS related_links (
                        id SERIAL PRIMARY KEY,
                        article_id INTEGER REFERENCES news_articles(id) ON DELETE CASCADE,
                        title VARCHAR(500),
                        url VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 인덱스 생성
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_news_articles_url ON news_articles(url)",
                    "CREATE INDEX IF NOT EXISTS idx_news_articles_crawled_at ON news_articles(crawled_at)",
                    "CREATE INDEX IF NOT EXISTS idx_news_articles_category ON news_articles(category)",
                    "CREATE INDEX IF NOT EXISTS idx_related_links_article_id ON related_links(article_id)"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                self.conn.commit()
                print("테이블이 성공적으로 생성되었습니다.")
                return True
                
        except psycopg2.Error as e:
            print(f"테이블 생성 실패: {e}")
            self.conn.rollback()
            return False
    
    def insert_article(self, article_data):
        """뉴스 기사 데이터 삽입"""
        try:
            with self.conn.cursor() as cursor:
                # 기사 데이터 삽입
                cursor.execute("""
                    INSERT INTO news_articles (url, title, content, author, publish_date, category, summary, crawled_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE SET
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        author = EXCLUDED.author,
                        publish_date = EXCLUDED.publish_date,
                        category = EXCLUDED.category,
                        summary = EXCLUDED.summary,
                        crawled_at = EXCLUDED.crawled_at,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    article_data.get('url'),
                    article_data.get('title'),
                    article_data.get('content'),
                    article_data.get('author'),
                    article_data.get('date'),
                    article_data.get('category'),
                    article_data.get('summary'),
                    article_data.get('crawled_at')
                ))
                
                article_id = cursor.fetchone()[0]
                
                # 관련 링크 삽입
                if 'related_links' in article_data and article_data['related_links']:
                    # 기존 관련 링크 삭제
                    cursor.execute("DELETE FROM related_links WHERE article_id = %s", (article_id,))
                    
                    # 새로운 관련 링크 삽입
                    for link in article_data['related_links']:
                        cursor.execute("""
                            INSERT INTO related_links (article_id, title, url)
                            VALUES (%s, %s, %s)
                        """, (article_id, link.get('title'), link.get('url')))
                
                self.conn.commit()
                print(f"기사가 성공적으로 저장되었습니다. (ID: {article_id})")
                return article_id
                
        except psycopg2.Error as e:
            print(f"기사 저장 실패: {e}")
            self.conn.rollback()
            return None
    
    def get_articles(self, limit=10):
        """저장된 기사 목록 조회"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, url, title, author, publish_date, category, crawled_at
                    FROM news_articles
                    ORDER BY crawled_at DESC
                    LIMIT %s
                """, (limit,))
                
                articles = cursor.fetchall()
                return articles
                
        except psycopg2.Error as e:
            print(f"기사 조회 실패: {e}")
            return []
    
    def search_articles(self, keyword, limit=10):
        """키워드로 기사 검색"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, url, title, author, publish_date, category, crawled_at
                    FROM news_articles
                    WHERE title ILIKE %s OR content ILIKE %s
                    ORDER BY crawled_at DESC
                    LIMIT %s
                """, (f'%{keyword}%', f'%{keyword}%', limit))
                
                articles = cursor.fetchall()
                return articles
                
        except psycopg2.Error as e:
            print(f"기사 검색 실패: {e}")
            return []
    
    def get_article_count(self):
        """저장된 기사 수 조회"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM news_articles")
                count = cursor.fetchone()[0]
                return count
        except psycopg2.Error as e:
            print(f"기사 수 조회 실패: {e}")
            return 0

def main():
    """데이터베이스 설정 및 테스트"""
    # 데이터베이스 연결 정보 설정
    db_manager = DatabaseManager(
        host='localhost',
        port=5432,
        database='news_crawler',
        user='postgres',
        password='your_password'  # 실제 비밀번호로 변경하세요
    )
    
    # 데이터베이스 연결
    if not db_manager.connect():
        print("데이터베이스 연결에 실패했습니다.")
        return
    
    try:
        # 테이블 생성
        if db_manager.create_tables():
            print("데이터베이스 설정이 완료되었습니다.")
            
            # 기사 수 확인
            count = db_manager.get_article_count()
            print(f"현재 저장된 기사 수: {count}")
            
            # 최근 기사 목록 조회
            articles = db_manager.get_articles(5)
            if articles:
                print("\n=== 최근 저장된 기사 ===")
                for article in articles:
                    print(f"- {article['title']} ({article['crawled_at']})")
    
    finally:
        db_manager.disconnect()

if __name__ == "__main__":
    main()
