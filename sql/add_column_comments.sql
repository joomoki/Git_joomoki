-- joomoki_news.news_articles 테이블 컬럼에 한글명(COMMENT) 추가

-- 1. news_articles 테이블 컬럼에 한글 설명 추가
COMMENT ON TABLE joomoki_news.news_articles IS '뉴스 기사 정보 테이블';

COMMENT ON COLUMN joomoki_news.news_articles.id IS '기사 고유 ID (자동증가)';
COMMENT ON COLUMN joomoki_news.news_articles.url IS '기사 URL (유니크)';
COMMENT ON COLUMN joomoki_news.news_articles.title IS '기사 제목';
COMMENT ON COLUMN joomoki_news.news_articles.content IS '기사 본문 내용';
COMMENT ON COLUMN joomoki_news.news_articles.author IS '기사 작성자';
COMMENT ON COLUMN joomoki_news.news_articles.publish_date IS '기사 발행일시';
COMMENT ON COLUMN joomoki_news.news_articles.category IS '뉴스 카테고리 (정치, 사회, 경제 등)';
COMMENT ON COLUMN joomoki_news.news_articles.summary IS '기사 요약';
COMMENT ON COLUMN joomoki_news.news_articles.crawled_at IS '크롤링된 시간';
COMMENT ON COLUMN joomoki_news.news_articles.created_at IS '레코드 생성 시간';
COMMENT ON COLUMN joomoki_news.news_articles.updated_at IS '레코드 수정 시간';

-- 2. related_links 테이블 컬럼에 한글 설명 추가
COMMENT ON TABLE joomoki_news.related_links IS '관련 기사 링크 테이블';

COMMENT ON COLUMN joomoki_news.related_links.id IS '관련 링크 고유 ID (자동증가)';
COMMENT ON COLUMN joomoki_news.related_links.article_id IS '기사 ID (외래키)';
COMMENT ON COLUMN joomoki_news.related_links.title IS '관련 기사 제목';
COMMENT ON COLUMN joomoki_news.related_links.url IS '관련 기사 URL';
COMMENT ON COLUMN joomoki_news.related_links.created_at IS '레코드 생성 시간';

-- 3. 인덱스에 한글 설명 추가
COMMENT ON INDEX joomoki_news.idx_news_articles_url IS '기사 URL 인덱스 (중복 방지용)';
COMMENT ON INDEX joomoki_news.idx_news_articles_crawled_at IS '크롤링 시간 인덱스 (시간순 조회용)';
COMMENT ON INDEX joomoki_news.idx_news_articles_category IS '카테고리 인덱스 (카테고리별 조회용)';
COMMENT ON INDEX joomoki_news.idx_related_links_article_id IS '기사 ID 인덱스 (관련 링크 조회용)';

-- 4. 컬럼 정보 확인 쿼리
SELECT 
    table_schema,
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default,
    col_description(pgc.oid, ordinal_position) as column_comment
FROM information_schema.columns isc
JOIN pg_class pgc ON pgc.relname = isc.table_name
WHERE table_schema = 'joomoki_news'
  AND table_name IN ('news_articles', 'related_links')
ORDER BY table_name, ordinal_position;
