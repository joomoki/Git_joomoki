-- 빠른 스키마 설정 스크립트
-- PostgreSQL에서 직접 실행하세요

-- 1. 스키마 생성
CREATE SCHEMA IF NOT EXISTS joomoki_news;

-- 2. 스키마 확인
SELECT 'Schema created: ' || schema_name as result
FROM information_schema.schemata 
WHERE schema_name = 'joomoki_news';

-- 3. 스키마 내 테이블 생성
CREATE TABLE IF NOT EXISTS joomoki_news.news_articles (
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
);

CREATE TABLE IF NOT EXISTS joomoki_news.related_links (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES joomoki_news.news_articles(id) ON DELETE CASCADE,
    title VARCHAR(500),
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_news_articles_url ON joomoki_news.news_articles(url);
CREATE INDEX IF NOT EXISTS idx_news_articles_crawled_at ON joomoki_news.news_articles(crawled_at);
CREATE INDEX IF NOT EXISTS idx_news_articles_category ON joomoki_news.news_articles(category);
CREATE INDEX IF NOT EXISTS idx_related_links_article_id ON joomoki_news.related_links(article_id);

-- 5. 검색 경로 설정 (선택사항)
-- ALTER DATABASE news_crawler SET search_path TO joomoki_news, public;

-- 6. 결과 확인
SELECT 
    'Tables in joomoki_news:' as info,
    table_name,
    'created' as status
FROM information_schema.tables 
WHERE table_schema = 'joomoki_news'
ORDER BY table_name;
