#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 스키마 관리 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

class SchemaManager:
    def __init__(self, host='localhost', port=5432, database='news_crawler', 
                 user='postgres', password='your_password'):
        """PostgreSQL 스키마 관리 클래스"""
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
    
    def create_schema(self, schema_name='joomoki_news'):
        """스키마 생성"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                self.conn.commit()
                print(f"스키마 '{schema_name}'이 생성되었습니다.")
                return True
        except psycopg2.Error as e:
            print(f"스키마 생성 실패: {e}")
            return False
    
    def create_tables_in_schema(self, schema_name='joomoki_news'):
        """스키마 내에 테이블 생성"""
        try:
            with self.conn.cursor() as cursor:
                # news_articles 테이블 생성
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.news_articles (
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
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {schema_name}.related_links (
                        id SERIAL PRIMARY KEY,
                        article_id INTEGER REFERENCES {schema_name}.news_articles(id) ON DELETE CASCADE,
                        title VARCHAR(500),
                        url VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 인덱스 생성
                indexes = [
                    f"CREATE INDEX IF NOT EXISTS idx_news_articles_url ON {schema_name}.news_articles(url)",
                    f"CREATE INDEX IF NOT EXISTS idx_news_articles_crawled_at ON {schema_name}.news_articles(crawled_at)",
                    f"CREATE INDEX IF NOT EXISTS idx_news_articles_category ON {schema_name}.news_articles(category)",
                    f"CREATE INDEX IF NOT EXISTS idx_related_links_article_id ON {schema_name}.related_links(article_id)"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                self.conn.commit()
                print(f"스키마 '{schema_name}'에 테이블이 생성되었습니다.")
                return True
                
        except psycopg2.Error as e:
            print(f"테이블 생성 실패: {e}")
            self.conn.rollback()
            return False
    
    def list_schemas(self):
        """모든 스키마 목록 조회"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    ORDER BY schema_name
                """)
                schemas = cursor.fetchall()
                return schemas
        except psycopg2.Error as e:
            print(f"스키마 목록 조회 실패: {e}")
            return []
    
    def list_tables_in_schema(self, schema_name='joomoki_news'):
        """특정 스키마의 테이블 목록 조회"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT table_name, table_type
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                    ORDER BY table_name
                """, (schema_name,))
                tables = cursor.fetchall()
                return tables
        except psycopg2.Error as e:
            print(f"테이블 목록 조회 실패: {e}")
            return []
    
    def drop_schema(self, schema_name='joomoki_news', cascade=False):
        """스키마 삭제"""
        try:
            with self.conn.cursor() as cursor:
                if cascade:
                    cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
                else:
                    cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name}")
                self.conn.commit()
                print(f"스키마 '{schema_name}'이 삭제되었습니다.")
                return True
        except psycopg2.Error as e:
            print(f"스키마 삭제 실패: {e}")
            return False
    
    def set_search_path(self, schema_name='joomoki_news'):
        """검색 경로 설정"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema_name}, public")
                self.conn.commit()
                print(f"검색 경로가 '{schema_name}, public'으로 설정되었습니다.")
                return True
        except psycopg2.Error as e:
            print(f"검색 경로 설정 실패: {e}")
            return False

def main():
    """스키마 관리 메인 함수"""
    # 스키마 관리자 생성
    schema_manager = SchemaManager(
        host='localhost',
        port=5432,
        database='news_crawler',
        user='postgres',
        password='your_password'  # 실제 비밀번호로 변경
    )
    
    # 데이터베이스 연결
    if not schema_manager.connect():
        print("데이터베이스 연결에 실패했습니다.")
        return
    
    try:
        # 1. 기존 스키마 목록 조회
        print("=== 기존 스키마 목록 ===")
        schemas = schema_manager.list_schemas()
        for schema in schemas:
            print(f"- {schema['schema_name']}")
        
        # 2. joomoki_news 스키마 생성
        schema_name = 'joomoki_news'
        if schema_manager.create_schema(schema_name):
            print(f"\n=== 스키마 '{schema_name}' 생성 완료 ===")
            
            # 3. 스키마 내에 테이블 생성
            if schema_manager.create_tables_in_schema(schema_name):
                print(f"=== 테이블 생성 완료 ===")
                
                # 4. 생성된 테이블 목록 확인
                tables = schema_manager.list_tables_in_schema(schema_name)
                print(f"\n=== 스키마 '{schema_name}'의 테이블 목록 ===")
                for table in tables:
                    print(f"- {table['table_name']} ({table['table_type']})")
                
                # 5. 검색 경로 설정
                schema_manager.set_search_path(schema_name)
        
        # 6. 최종 스키마 목록 확인
        print(f"\n=== 최종 스키마 목록 ===")
        schemas = schema_manager.list_schemas()
        for schema in schemas:
            print(f"- {schema['schema_name']}")
    
    finally:
        schema_manager.disconnect()

if __name__ == "__main__":
    main()
