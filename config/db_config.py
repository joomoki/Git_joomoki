#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 연결 설정 파일
"""

# PostgreSQL 데이터베이스 연결 설정
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'news_crawler',
    'user': 'postgres',
    'password': 'wnahr!1149'
}

# 스키마 설정
SCHEMA_NAME = 'joomoki_news'

# 테이블 설정
TABLES = {
    'articles': 'news_articles',
    'related_links': 'related_links'
}

# 크롤링 설정
CRAWLING_CONFIG = {
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'timeout': 30,
    'delay': 1  # 요청 간 딜레이 (초)
}

# 파일 저장 설정
FILE_CONFIG = {
    'backup_dir': r'D:\joomoki_PJ\WCD',
    'json_filename': 'daum_news_article.json'
}
