#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다음뉴스 크롤링 스크립트
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re
import os

class DaumNewsCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def crawl_article(self, url):
        """
        다음뉴스 기사를 크롤링합니다.
        
        Args:
            url (str): 크롤링할 기사 URL
            
        Returns:
            dict: 크롤링된 기사 정보
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 기사 정보 추출
            article_data = {
                'url': url,
                'crawled_at': datetime.now().isoformat(),
                'title': self._extract_title(soup),
                'author': self._extract_author(soup),
                'date': self._extract_date(soup),
                'category': self._extract_category(soup),
                'content': self._extract_content(soup),
                'summary': self._extract_summary(soup),
                'related_links': self._extract_related_links(soup)
            }
            
            return article_data
            
        except Exception as e:
            print(f"크롤링 중 오류 발생: {e}")
            return None
    
    def _extract_title(self, soup):
        """제목 추출"""
        title_selectors = [
            'h3.tit_view',
            'h1.tit_view',
            '.tit_view',
            'h3',
            'h1'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)
        
        return "제목을 찾을 수 없습니다."
    
    def _extract_author(self, soup):
        """작성자 추출"""
        author_selectors = [
            '.info_view .txt_info',
            '.info_view .author',
            '.author',
            '.byline'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = author_elem.get_text(strip=True)
                # "기자" 앞의 이름만 추출
                if '기자' in author_text:
                    return author_text.split('기자')[0].strip() + ' 기자'
                return author_text
        
        return "작성자 정보 없음"
    
    def _extract_date(self, soup):
        """작성일시 추출"""
        date_selectors = [
            '.info_view .txt_info',
            '.date',
            '.timestamp'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                # 날짜 패턴 찾기
                date_pattern = r'\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.\s*\d{1,2}:\d{2}'
                match = re.search(date_pattern, date_text)
                if match:
                    return match.group()
        
        return "날짜 정보 없음"
    
    def _extract_category(self, soup):
        """카테고리 추출"""
        category_selectors = [
            '.tit_cate',
            '.category',
            '.breadcrumb a'
        ]
        
        for selector in category_selectors:
            category_elem = soup.select_one(selector)
            if category_elem:
                return category_elem.get_text(strip=True)
        
        return "카테고리 정보 없음"
    
    def _extract_content(self, soup):
        """본문 내용 추출"""
        content_selectors = [
            '.news_view .news_view_fot',
            '.news_view',
            '.article_view',
            '.content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # 광고나 불필요한 요소 제거
                for unwanted in content_elem.select('.ad, .advertisement, .related, .recommend'):
                    unwanted.decompose()
                
                return content_elem.get_text(strip=True, separator='\n')
        
        return "본문을 찾을 수 없습니다."
    
    def _extract_summary(self, soup):
        """요약 정보 추출"""
        summary_selectors = [
            '.summary',
            '.auto_summary',
            '.article_summary'
        ]
        
        for selector in summary_selectors:
            summary_elem = soup.select_one(selector)
            if summary_elem:
                return summary_elem.get_text(strip=True)
        
        return "요약 정보 없음"
    
    def _extract_related_links(self, soup):
        """관련 링크 추출"""
        related_links = []
        
        # 관련 기사 링크들
        link_selectors = [
            '.related_news a',
            '.recommend_news a',
            '.list_news a'
        ]
        
        for selector in link_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)
                if href and text:
                    related_links.append({
                        'title': text,
                        'url': href
                    })
        
        return related_links
    
    def save_to_json(self, data, filename):
        """데이터를 JSON 파일로 저장"""
        # 저장할 디렉토리 생성
        save_dir = r"D:\joomoki_PJ\WCD"
        os.makedirs(save_dir, exist_ok=True)
        
        # 전체 경로 생성
        full_path = os.path.join(save_dir, filename)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"데이터가 {full_path}에 저장되었습니다.")

def main():
    """메인 함수"""
    crawler = DaumNewsCrawler()
    
    # 크롤링할 URL
    url = "https://v.daum.net/v/20250927201941985"
    
    print(f"다음뉴스 기사 크롤링 시작: {url}")
    
    # 기사 크롤링
    article_data = crawler.crawl_article(url)
    
    if article_data:
        print("\n=== 크롤링 결과 ===")
        print(f"제목: {article_data['title']}")
        print(f"작성자: {article_data['author']}")
        print(f"작성일: {article_data['date']}")
        print(f"카테고리: {article_data['category']}")
        print(f"본문 길이: {len(article_data['content'])} 문자")
        print(f"관련 링크 수: {len(article_data['related_links'])}")
        
        # JSON 파일로 저장
        crawler.save_to_json(article_data, 'daum_news_article.json')
        
        # 본문 일부 출력
        print(f"\n=== 본문 일부 ===")
        print(article_data['content'][:500] + "..." if len(article_data['content']) > 500 else article_data['content'])
        
    else:
        print("크롤링에 실패했습니다.")

if __name__ == "__main__":
    main()
