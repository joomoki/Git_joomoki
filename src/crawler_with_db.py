#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다음뉴스 크롤링 + PostgreSQL 저장 스크립트
"""

import urllib.request
import urllib.parse
import json
import re
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

class DaumNewsCrawlerWithDB:
    def __init__(self, db_config=None):
        """
        크롤링 + DB 저장 클래스
        
        Args:
            db_config: 데이터베이스 연결 설정
        """
        self.db_config = db_config or {
            'host': 'localhost',
            'port': 5432,
            'database': 'news_crawler',
            'user': 'postgres',
            'password': 'wnahr!1149'
        }
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
    
    def crawl_article(self, url):
        """다음뉴스 기사를 크롤링합니다."""
        try:
            # User-Agent 설정
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 요청 생성
            req = urllib.request.Request(url, headers=headers)
            
            # 웹페이지 가져오기
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
            
            # 기본 정보 추출
            article_data = {
                'url': url,
                'crawled_at': datetime.now().isoformat(),
                'title': self._extract_title(html),
                'content': self._extract_content(html),
                'author': self._extract_author(html),
                'publish_date': self._extract_date(html),
                'category': self._extract_category(html),
                'summary': self._extract_summary(html),
                'related_links': self._extract_related_links(html),
                'raw_html_length': len(html)
            }
            
            return article_data
            
        except Exception as e:
            print(f"크롤링 중 오류 발생: {e}")
            return None
    
    def _extract_title(self, html):
        """제목 추출"""
        title_patterns = [
            r'<h3[^>]*class="[^"]*tit_view[^"]*"[^>]*>(.*?)</h3>',
            r'<h1[^>]*class="[^"]*tit_view[^"]*"[^>]*>(.*?)</h1>',
            r'<title>(.*?)</title>',
            r'<h3[^>]*>(.*?)</h3>',
            r'<h1[^>]*>(.*?)</h1>'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                title = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                if title and len(title) > 10:
                    return title
        
        return "제목을 찾을 수 없습니다."
    
    def _extract_author(self, html):
        """작성자 추출"""
        author_patterns = [
            r'<span[^>]*class="[^"]*txt_info[^"]*"[^>]*>(.*?)</span>',
            r'<span[^>]*class="[^"]*author[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^"]*byline[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                author_text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                if '기자' in author_text:
                    return author_text.split('기자')[0].strip() + ' 기자'
                return author_text
        
        return "작성자 정보 없음"
    
    def _extract_date(self, html):
        """작성일시 추출"""
        date_patterns = [
            r'<span[^>]*class="[^"]*txt_info[^"]*"[^>]*>(.*?)</span>',
            r'<span[^>]*class="[^"]*date[^"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^"]*timestamp[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                date_text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                # 날짜 패턴 찾기
                date_pattern = r'\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.\s*\d{1,2}:\d{2}'
                date_match = re.search(date_pattern, date_text)
                if date_match:
                    return date_match.group()
        
        return "날짜 정보 없음"
    
    def _extract_category(self, html):
        """카테고리 추출"""
        category_patterns = [
            r'<span[^>]*class="[^"]*tit_cate[^"]*"[^>]*>(.*?)</span>',
            r'<span[^>]*class="[^"]*category[^"]*"[^>]*>(.*?)</span>',
            r'<a[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</a>'
        ]
        
        for pattern in category_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                category = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                if category:
                    return category
        
        return "카테고리 정보 없음"
    
    def _extract_content(self, html):
        """본문 내용 추출"""
        content_patterns = [
            r'<div[^>]*class="[^"]*news_view[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*article_view[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in content_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                # HTML 태그 제거
                content = re.sub(r'<[^>]+>', ' ', content)
                # 여러 공백을 하나로
                content = re.sub(r'\s+', ' ', content).strip()
                if content and len(content) > 100:
                    return content
        
        return "본문을 찾을 수 없습니다."
    
    def _extract_summary(self, html):
        """요약 정보 추출"""
        summary_patterns = [
            r'<div[^>]*class="[^"]*summary[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*auto_summary[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*article_summary[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                summary = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                if summary:
                    return summary
        
        return "요약 정보 없음"
    
    def _extract_related_links(self, html):
        """관련 링크 추출"""
        related_links = []
        
        # 관련 기사 링크들
        link_patterns = [
            r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*related_news[^"]*"[^>]*>(.*?)</a>',
            r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*recommend_news[^"]*"[^>]*>(.*?)</a>',
            r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*list_news[^"]*"[^>]*>(.*?)</a>'
        ]
        
        for pattern in link_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            for href, text in matches:
                if href and text:
                    related_links.append({
                        'title': re.sub(r'<[^>]+>', '', text).strip(),
                        'url': href
                    })
        
        return related_links
    
    def save_to_database(self, article_data):
        """크롤링된 데이터를 PostgreSQL에 저장"""
        try:
            with self.conn.cursor() as cursor:
                # 기사 데이터 삽입
                cursor.execute("""
                    INSERT INTO joomoki_news.news_articles (url, title, content, author, publish_date, category, summary, crawled_at)
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
                    article_data.get('publish_date'),
                    article_data.get('category'),
                    article_data.get('summary'),
                    article_data.get('crawled_at')
                ))
                
                article_id = cursor.fetchone()[0]
                
                # 관련 링크 삽입
                if 'related_links' in article_data and article_data['related_links']:
                    # 기존 관련 링크 삭제
                    cursor.execute("DELETE FROM joomoki_news.related_links WHERE article_id = %s", (article_id,))
                    
                    # 새로운 관련 링크 삽입
                    for link in article_data['related_links']:
                        cursor.execute("""
                            INSERT INTO joomoki_news.related_links (article_id, title, url)
                            VALUES (%s, %s, %s)
                        """, (article_id, link.get('title'), link.get('url')))
                
                self.conn.commit()
                print(f"기사가 성공적으로 DB에 저장되었습니다. (ID: {article_id})")
                return article_id
                
        except psycopg2.Error as e:
            print(f"DB 저장 실패: {e}")
            self.conn.rollback()
            return None
    
    def save_to_json(self, data, filename):
        """데이터를 JSON 파일로도 저장 (백업용)"""
        save_dir = r"D:\joomoki_PJ\WCD"
        os.makedirs(save_dir, exist_ok=True)
        
        full_path = os.path.join(save_dir, filename)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"데이터가 {full_path}에 백업 저장되었습니다.")
    
    def get_article_count(self):
        """저장된 기사 수 조회"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM joomoki_news.news_articles")
                count = cursor.fetchone()[0]
                return count
        except psycopg2.Error as e:
            print(f"기사 수 조회 실패: {e}")
            return 0
    
    def get_recent_articles(self, limit=5):
        """최근 저장된 기사 목록 조회"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, url, title, author, publish_date, category, crawled_at
                    FROM joomoki_news.news_articles
                    ORDER BY crawled_at DESC
                    LIMIT %s
                """, (limit,))
                
                articles = cursor.fetchall()
                return articles
        except psycopg2.Error as e:
            print(f"기사 조회 실패: {e}")
            return []

def main():
    """메인 함수"""
    # 크롤링할 URL
    url = "https://v.daum.net/v/20250927201941985"
    
    # 크롤러 생성
    crawler = DaumNewsCrawlerWithDB()
    
    print(f"다음뉴스 기사 크롤링 시작: {url}")
    
    # 데이터베이스 연결
    if not crawler.connect_db():
        print("데이터베이스 연결에 실패했습니다.")
        return
    
    try:
        # 기사 크롤링
        article_data = crawler.crawl_article(url)
        
        if article_data:
            print("\n=== 크롤링 결과 ===")
            print(f"제목: {article_data['title']}")
            print(f"작성자: {article_data['author']}")
            print(f"작성일: {article_data['publish_date']}")
            print(f"카테고리: {article_data['category']}")
            print(f"본문 길이: {len(article_data['content'])} 문자")
            print(f"관련 링크 수: {len(article_data['related_links'])}")
            
            # 데이터베이스에 저장
            article_id = crawler.save_to_database(article_data)
            
            if article_id:
                # JSON 파일로도 백업 저장
                crawler.save_to_json(article_data, 'daum_news_article.json')
                
                # 저장된 기사 수 확인
                total_count = crawler.get_article_count()
                print(f"\n현재 DB에 저장된 총 기사 수: {total_count}")
                
                # 최근 기사 목록 조회
                recent_articles = crawler.get_recent_articles(3)
                if recent_articles:
                    print("\n=== 최근 저장된 기사 ===")
                    for article in recent_articles:
                        print(f"- {article['title']} ({article['crawled_at']})")
                
                # 본문 일부 출력
                print(f"\n=== 본문 일부 ===")
                content = article_data['content']
                if len(content) > 500:
                    print(content[:500] + "...")
                else:
                    print(content)
            else:
                print("데이터베이스 저장에 실패했습니다.")
        else:
            print("크롤링에 실패했습니다.")
    
    finally:
        crawler.disconnect_db()

if __name__ == "__main__":
    main()
