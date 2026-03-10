-- 주식 분석을 위한 스키마 및 테이블 생성

-- 1. 주식 종목 정보 테이블
CREATE TABLE IF NOT EXISTS joomoki_news.stock_companies (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) UNIQUE NOT NULL,  -- 종목코드 (예: 005930)
    company_name VARCHAR(100) NOT NULL,      -- 회사명 (예: 삼성전자)
    market_type VARCHAR(20),                 -- 시장구분 (KOSPI, KOSDAQ, KONEX)
    sector VARCHAR(50),                      -- 업종
    market_cap BIGINT,                       -- 시가총액
    listed_date DATE,                        -- 상장일
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 주식 가격 데이터 테이블
CREATE TABLE IF NOT EXISTS joomoki_news.stock_prices (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(10,2),               -- 시가
    high_price DECIMAL(10,2),               -- 고가
    low_price DECIMAL(10,2),                -- 저가
    close_price DECIMAL(10,2),              -- 종가
    volume BIGINT,                          -- 거래량
    market_cap BIGINT,                      -- 시가총액
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES joomoki_news.stock_companies(stock_code),
    UNIQUE(stock_code, trade_date)
);

-- 3. 뉴스-주식 종목 연결 테이블 (N:M 관계)
CREATE TABLE IF NOT EXISTS joomoki_news.news_stock_relations (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    relevance_score DECIMAL(3,2) DEFAULT 1.0,  -- 관련도 점수 (0.0-1.0)
    sentiment_score DECIMAL(3,2),              -- 감정 점수 (-1.0~1.0, 음수=부정, 양수=긍정)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES joomoki_news.news_articles(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_code) REFERENCES joomoki_news.stock_companies(stock_code),
    UNIQUE(article_id, stock_code)
);

-- 4. 주식 키워드 테이블 (뉴스에서 추출된 키워드)
CREATE TABLE IF NOT EXISTS joomoki_news.stock_keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) NOT NULL,
    stock_code VARCHAR(10),
    frequency INTEGER DEFAULT 1,
    last_mentioned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES joomoki_news.stock_companies(stock_code)
);

-- 5. 주식 분석 결과 테이블
CREATE TABLE IF NOT EXISTS joomoki_news.stock_analysis (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    analysis_date DATE NOT NULL,
    news_impact_score DECIMAL(5,2),         -- 뉴스 영향도 점수
    sentiment_trend VARCHAR(20),            -- 감정 트렌드 (POSITIVE, NEGATIVE, NEUTRAL)
    price_prediction VARCHAR(20),           -- 가격 예측 (UP, DOWN, HOLD)
    confidence_level DECIMAL(3,2),          -- 신뢰도 (0.0-1.0)
    analysis_summary TEXT,                  -- 분석 요약
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES joomoki_news.stock_companies(stock_code),
    UNIQUE(stock_code, analysis_date)
);

-- 6. 주식 기본/수급 정보 테이블 (일별 상세)
CREATE TABLE IF NOT EXISTS joomoki_news.stock_fundamentals (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    base_date DATE NOT NULL,
    per DECIMAL(10,2),                      -- PER (주가수익비율)
    pbr DECIMAL(10,2),                      -- PBR (주가순자산비율)
    eps DECIMAL(10,2),                      -- EPS (주당순이익)
    bps DECIMAL(10,2),                      -- BPS (주당순자산가치)
    market_cap BIGINT,                      -- 시가총액 (억 원 단위 등으로 저장하지 말고 원 단위)
    shares_outstanding BIGINT,              -- 상장주식수
    foreigner_net_buy BIGINT,               -- 외국인 순매수 수량
    program_net_buy BIGINT,                 -- 프로그램 순매수 수량
    foreigner_exhaustion_rate DECIMAL(5,2), -- 외국인 소진율
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES joomoki_news.stock_companies(stock_code),
    UNIQUE(stock_code, base_date)
);

-- 6. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_stock_companies_code ON joomoki_news.stock_companies(stock_code);
CREATE INDEX IF NOT EXISTS idx_stock_companies_name ON joomoki_news.stock_companies(company_name);
CREATE INDEX IF NOT EXISTS idx_stock_prices_code_date ON joomoki_news.stock_prices(stock_code, trade_date);
CREATE INDEX IF NOT EXISTS idx_news_stock_relations_article ON joomoki_news.news_stock_relations(article_id);
CREATE INDEX IF NOT EXISTS idx_news_stock_relations_stock ON joomoki_news.news_stock_relations(stock_code);
CREATE INDEX IF NOT EXISTS idx_stock_keywords_keyword ON joomoki_news.stock_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_stock_analysis_code_date ON joomoki_news.stock_analysis(stock_code, analysis_date);
CREATE INDEX IF NOT EXISTS idx_stock_fundamentals_code_date ON joomoki_news.stock_fundamentals(stock_code, base_date);

-- 7. 테이블 설명 추가
COMMENT ON TABLE joomoki_news.stock_companies IS '주식 종목 정보 테이블';
COMMENT ON TABLE joomoki_news.stock_prices IS '주식 가격 데이터 테이블';
COMMENT ON TABLE joomoki_news.news_stock_relations IS '뉴스-주식 종목 연결 테이블';
COMMENT ON TABLE joomoki_news.stock_keywords IS '주식 관련 키워드 테이블';
COMMENT ON TABLE joomoki_news.stock_analysis IS '주식 분석 결과 테이블';

-- 8. 컬럼 설명 추가
COMMENT ON COLUMN joomoki_news.stock_companies.stock_code IS '종목코드 (6자리)';
COMMENT ON COLUMN joomoki_news.stock_companies.company_name IS '회사명';
COMMENT ON COLUMN joomoki_news.stock_companies.market_type IS '시장구분 (KOSPI/KOSDAQ/KONEX)';
COMMENT ON COLUMN joomoki_news.stock_companies.sector IS '업종';
COMMENT ON COLUMN joomoki_news.stock_companies.market_cap IS '시가총액';

COMMENT ON COLUMN joomoki_news.stock_prices.trade_date IS '거래일';
COMMENT ON COLUMN joomoki_news.stock_prices.open_price IS '시가';
COMMENT ON COLUMN joomoki_news.stock_prices.high_price IS '고가';
COMMENT ON COLUMN joomoki_news.stock_prices.low_price IS '저가';
COMMENT ON COLUMN joomoki_news.stock_prices.close_price IS '종가';
COMMENT ON COLUMN joomoki_news.stock_prices.volume IS '거래량';

COMMENT ON COLUMN joomoki_news.news_stock_relations.relevance_score IS '뉴스-종목 관련도 (0.0-1.0)';
COMMENT ON COLUMN joomoki_news.news_stock_relations.sentiment_score IS '감정 점수 (-1.0~1.0)';

COMMENT ON COLUMN joomoki_news.stock_analysis.news_impact_score IS '뉴스 영향도 점수';
COMMENT ON COLUMN joomoki_news.stock_analysis.sentiment_trend IS '감정 트렌드';
COMMENT ON COLUMN joomoki_news.stock_analysis.price_prediction IS '가격 예측';
COMMENT ON COLUMN joomoki_news.stock_analysis.confidence_level IS '신뢰도 (0.0-1.0)';
