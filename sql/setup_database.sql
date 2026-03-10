-- PostgreSQL 데이터베이스 및 테이블 생성 스크립트

-- 1. 데이터베이스 생성 (관리자 권한으로 실행)
-- CREATE DATABASE news_crawler;

-- 2. 데이터베이스에 연결 후 실행할 SQL

-- 크롤링된 뉴스 기사를 저장할 테이블 생성
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
);

-- 인덱스 생성 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_news_articles_url ON news_articles(url);
CREATE INDEX IF NOT EXISTS idx_news_articles_title ON news_articles USING gin(to_tsvector('korean', title));
CREATE INDEX IF NOT EXISTS idx_news_articles_content ON news_articles USING gin(to_tsvector('korean', content));
CREATE INDEX IF NOT EXISTS idx_news_articles_crawled_at ON news_articles(crawled_at);
CREATE INDEX IF NOT EXISTS idx_news_articles_category ON news_articles(category);

-- 관련 링크를 저장할 테이블 생성
CREATE TABLE IF NOT EXISTS related_links (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES news_articles(id) ON DELETE CASCADE,
    title VARCHAR(500),
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 관련 링크 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_related_links_article_id ON related_links(article_id);

-- 테이블 생성 확인
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('news_articles', 'related_links')
ORDER BY table_name, ordinal_position;

-- 샘플 데이터 확인용 쿼리
-- SELECT COUNT(*) as total_articles FROM news_articles;
-- SELECT * FROM news_articles ORDER BY crawled_at DESC LIMIT 5;
