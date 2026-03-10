-- us_stock_companies 테이블에 major_index 컬럼 추가 (지수 정보 저장용)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'joomoki_news'
        AND table_name = 'us_stock_companies'
        AND column_name = 'major_index'
    ) THEN
        ALTER TABLE joomoki_news.us_stock_companies ADD COLUMN major_index VARCHAR(50);
        COMMENT ON COLUMN joomoki_news.us_stock_companies.major_index IS '주요 지수 (S&P500, Dow30, Nasdaq100 등)';
    END IF;
END $$;
