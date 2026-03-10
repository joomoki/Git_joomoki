#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 데이터베이스 연결 테스트 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import DB_CONFIG, SCHEMA_NAME

def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ 데이터베이스 연결 성공!")
        
        with conn.cursor() as cursor:
            # 데이터베이스 정보 조회
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"📊 PostgreSQL 버전: {version}")
            
            # 스키마 존재 확인
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, (SCHEMA_NAME,))
            
            schema_exists = cursor.fetchone()
            if schema_exists:
                print(f"✅ 스키마 '{SCHEMA_NAME}' 존재 확인")
                
                # 테이블 목록 조회
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                    ORDER BY table_name
                """, (SCHEMA_NAME,))
                
                tables = cursor.fetchall()
                print(f"📋 테이블 목록:")
                for table in tables:
                    print(f"  - {table[0]}")
                
                # 기사 수 조회
                cursor.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.news_articles")
                article_count = cursor.fetchone()[0]
                print(f"📰 저장된 기사 수: {article_count}")
                
                # 최근 기사 조회
                cursor.execute(f"""
                    SELECT title, crawled_at 
                    FROM {SCHEMA_NAME}.news_articles 
                    ORDER BY crawled_at DESC 
                    LIMIT 3
                """)
                
                recent_articles = cursor.fetchall()
                if recent_articles:
                    print(f"📄 최근 기사:")
                    for article in recent_articles:
                        print(f"  - {article[0]} ({article[1]})")
                else:
                    print("📄 저장된 기사가 없습니다.")
                    
            else:
                print(f"❌ 스키마 '{SCHEMA_NAME}'가 존재하지 않습니다.")
                print("스키마를 먼저 생성해주세요:")
                print("  python schema_management.py")
                print("  또는")
                print("  psql -U postgres -d news_crawler -f quick_schema_setup.sql")
        
        conn.close()
        print("✅ 데이터베이스 연결 종료")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print("\n해결 방법:")
        print("1. PostgreSQL이 실행 중인지 확인")
        print("2. db_config.py에서 연결 정보 확인")
        print("3. 데이터베이스 'news_crawler'가 생성되었는지 확인")
        print("4. 스키마 'joomoki_news'가 생성되었는지 확인")
        return False

def main():
    """메인 함수"""
    print("🔍 PostgreSQL 데이터베이스 연결 테스트 시작...")
    print(f"📡 연결 정보: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"👤 사용자: {DB_CONFIG['user']}")
    print(f"🗂️ 스키마: {SCHEMA_NAME}")
    print("-" * 50)
    
    success = test_connection()
    
    if success:
        print("\n🎉 모든 테스트가 성공했습니다!")
        print("이제 크롤링을 실행할 수 있습니다:")
        print("  python crawler_with_db.py")
    else:
        print("\n❌ 테스트에 실패했습니다.")
        print("위의 해결 방법을 참고하여 문제를 해결해주세요.")

if __name__ == "__main__":
    main()
