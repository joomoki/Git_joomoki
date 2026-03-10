#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테이블 컬럼에 한글명(COMMENT) 추가하는 Python 스크립트
"""

import psycopg2
from db_config import DB_CONFIG, SCHEMA_NAME

def add_table_comments():
    """테이블과 컬럼에 한글 설명 추가"""
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"✅ 데이터베이스 '{DB_CONFIG['database']}'에 연결되었습니다.")
        
        with conn.cursor() as cursor:
            # 1. 테이블 설명 추가
            table_comments = [
                (f"{SCHEMA_NAME}.news_articles", "뉴스 기사 정보 테이블"),
                (f"{SCHEMA_NAME}.related_links", "관련 기사 링크 테이블")
            ]
            
            for table, comment in table_comments:
                cursor.execute(f"COMMENT ON TABLE {table} IS %s", (comment,))
                print(f"📋 테이블 설명 추가: {table} - {comment}")
            
            # 2. news_articles 컬럼 설명 추가
            news_articles_comments = [
                ("id", "기사 고유 ID (자동증가)"),
                ("url", "기사 URL (유니크)"),
                ("title", "기사 제목"),
                ("content", "기사 본문 내용"),
                ("author", "기사 작성자"),
                ("publish_date", "기사 발행일시"),
                ("category", "뉴스 카테고리 (정치, 사회, 경제 등)"),
                ("summary", "기사 요약"),
                ("crawled_at", "크롤링된 시간"),
                ("created_at", "레코드 생성 시간"),
                ("updated_at", "레코드 수정 시간")
            ]
            
            for column, comment in news_articles_comments:
                cursor.execute(f"COMMENT ON COLUMN {SCHEMA_NAME}.news_articles.{column} IS %s", (comment,))
                print(f"📝 컬럼 설명 추가: news_articles.{column} - {comment}")
            
            # 3. related_links 컬럼 설명 추가
            related_links_comments = [
                ("id", "관련 링크 고유 ID (자동증가)"),
                ("article_id", "기사 ID (외래키)"),
                ("title", "관련 기사 제목"),
                ("url", "관련 기사 URL"),
                ("created_at", "레코드 생성 시간")
            ]
            
            for column, comment in related_links_comments:
                cursor.execute(f"COMMENT ON COLUMN {SCHEMA_NAME}.related_links.{column} IS %s", (comment,))
                print(f"📝 컬럼 설명 추가: related_links.{column} - {comment}")
            
            # 4. 인덱스 설명 추가
            index_comments = [
                ("idx_news_articles_url", "기사 URL 인덱스 (중복 방지용)"),
                ("idx_news_articles_crawled_at", "크롤링 시간 인덱스 (시간순 조회용)"),
                ("idx_news_articles_category", "카테고리 인덱스 (카테고리별 조회용)"),
                ("idx_related_links_article_id", "기사 ID 인덱스 (관련 링크 조회용)")
            ]
            
            for index, comment in index_comments:
                cursor.execute(f"COMMENT ON INDEX {SCHEMA_NAME}.{index} IS %s", (comment,))
                print(f"🔍 인덱스 설명 추가: {index} - {comment}")
            
            # 변경사항 커밋
            conn.commit()
            print("\n✅ 모든 설명이 성공적으로 추가되었습니다!")
            
            # 5. 결과 확인
            print("\n📊 추가된 설명 확인:")
            cursor.execute("""
                SELECT 
                    table_name as "테이블명",
                    column_name as "컬럼명",
                    col_description(pgc.oid, ordinal_position) as "설명"
                FROM information_schema.columns isc
                JOIN pg_class pgc ON pgc.relname = isc.table_name
                WHERE table_schema = %s
                ORDER BY table_name, ordinal_position
            """, (SCHEMA_NAME,))
            
            results = cursor.fetchall()
            current_table = None
            for row in results:
                table_name, column_name, comment = row
                if current_table != table_name:
                    print(f"\n📋 {table_name} 테이블:")
                    current_table = table_name
                print(f"  - {column_name}: {comment}")
        
        conn.close()
        print("\n🎉 작업이 완료되었습니다!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    print("🔧 테이블 컬럼에 한글명(COMMENT) 추가 시작...")
    print(f"🗂️ 대상 스키마: {SCHEMA_NAME}")
    print("-" * 50)
    
    success = add_table_comments()
    
    if success:
        print("\n✅ 모든 작업이 성공적으로 완료되었습니다!")
        print("이제 테이블 구조를 확인할 수 있습니다:")
        print("  psql -U postgres -d news_crawler -f view_table_structure.sql")
    else:
        print("\n❌ 작업 중 오류가 발생했습니다.")

if __name__ == "__main__":
    main()
