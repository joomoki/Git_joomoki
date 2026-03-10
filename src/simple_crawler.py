#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 다음뉴스 크롤링 스크립트 (라이브러리 없이)
"""

import urllib.request
import urllib.parse
import json
import re
import os
from datetime import datetime

def crawl_daum_news(url):
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
            'title': extract_title(html),
            'content': extract_content(html),
            'raw_html_length': len(html)
        }
        
        return article_data
        
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
        return None

def extract_title(html):
    """제목 추출"""
    # 다양한 제목 패턴 시도
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
            if title and len(title) > 10:  # 의미있는 제목인지 확인
                return title
    
    return "제목을 찾을 수 없습니다."

def extract_content(html):
    """본문 내용 추출"""
    # 본문 패턴들
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
            if content and len(content) > 100:  # 의미있는 내용인지 확인
                return content
    
    return "본문을 찾을 수 없습니다."

def save_to_json(data, filename):
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
    # 크롤링할 URL
    url = "https://v.daum.net/v/20250927201941985"
    
    print(f"다음뉴스 기사 크롤링 시작: {url}")
    
    # 기사 크롤링
    article_data = crawl_daum_news(url)
    
    if article_data:
        print("\n=== 크롤링 결과 ===")
        print(f"제목: {article_data['title']}")
        print(f"본문 길이: {len(article_data['content'])} 문자")
        print(f"HTML 길이: {article_data['raw_html_length']} 문자")
        
        # JSON 파일로 저장
        save_to_json(article_data, 'daum_news_article.json')
        
        # 본문 일부 출력
        print(f"\n=== 본문 일부 ===")
        content = article_data['content']
        if len(content) > 500:
            print(content[:500] + "...")
        else:
            print(content)
        
    else:
        print("크롤링에 실패했습니다.")

if __name__ == "__main__":
    main()
