-- 1. us_stock_companies 테이블에 korean_name 컬럼 추가 (없을 경우에만)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'joomoki_news'
        AND table_name = 'us_stock_companies'
        AND column_name = 'korean_name'
    ) THEN
        ALTER TABLE joomoki_news.us_stock_companies ADD COLUMN korean_name VARCHAR(100);
        COMMENT ON COLUMN joomoki_news.us_stock_companies.korean_name IS '한글 종목명';
    END IF;
END $$;

-- 2. us_stock_news 테이블 생성 (이미 존재하면 건너뜀 - create_us_stock_schema.sql 내용과 동일하지만 안전을 위해)
CREATE TABLE IF NOT EXISTS joomoki_news.us_stock_news (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    news_date TIMESTAMP NOT NULL,            -- 뉴스 발행 일시
    title VARCHAR(500) NOT NULL,             -- 뉴스 제목
    link VARCHAR(1000),                      -- 뉴스 링크
    source VARCHAR(100),                     -- 뉴스 출처
    sentiment_score FLOAT,                   -- 감성 점수 (-1.0 ~ 1.0)
    sentiment_label VARCHAR(20),             -- 감성 라벨 (Positive, Negative, Neutral)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, title)                -- 중복 뉴스 방지
);
