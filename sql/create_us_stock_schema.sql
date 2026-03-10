-- 미국 주식 분석을 위한 스키마 및 테이블 생성

-- 1. 미국 주식 종목 정보 테이블
CREATE TABLE IF NOT EXISTS joomoki_news.us_stock_companies (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) UNIQUE NOT NULL,  -- 종목코드 (예: AAPL, TSLA)
    company_name VARCHAR(100) NOT NULL,      -- 회사명 (예: Apple Inc.)
    korean_name VARCHAR(100),                -- 한글 회사명 (예: 애플)
    market_type VARCHAR(20),                 -- 시장구분 (NAS, NYS, AMS)
    sector VARCHAR(100),                     -- 업종 (Crowding, ETF 등)
    industry VARCHAR(100),                   -- 산업분류
    market_cap BIGINT,                       -- 시가총액 (달러 기준)
    currency VARCHAR(10) DEFAULT 'USD',      -- 통화
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 미국 주식 뉴스 및 감성 분석 테이블
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
    FOREIGN KEY (stock_code) REFERENCES joomoki_news.us_stock_companies(stock_code),
    UNIQUE(stock_code, title)                -- 중복 뉴스 방지
);

-- 2. 미국 주식 가격 데이터 테이블
CREATE TABLE IF NOT EXISTS joomoki_news.us_stock_prices (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(15,4),               -- 시가
    high_price DECIMAL(15,4),               -- 고가
    low_price DECIMAL(15,4),                -- 저가
    close_price DECIMAL(15,4),              -- 종가
    volume BIGINT,                          -- 거래량
    adj_close_price DECIMAL(15,4),          -- 수정 종가
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES joomoki_news.us_stock_companies(stock_code),
    UNIQUE(stock_code, trade_date)
);

-- 3. 미국 주식 분석 결과 테이블 (AI 분석 등)
CREATE TABLE IF NOT EXISTS joomoki_news.us_stock_analysis (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    analysis_date DATE NOT NULL,
    summary TEXT,                           -- 분석 요약
    sentiment_score DECIMAL(5,2),           -- 감정 점수
    price_prediction VARCHAR(20),           -- 가격 예측 (UP, DOWN, HOLD)
    confidence DECIMAL(3,2),                -- 신뢰도 (0.0-1.0)
    signals JSONB,                          -- 기술적/기본적 신호들 (JSON)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES joomoki_news.us_stock_companies(stock_code),
    UNIQUE(stock_code, analysis_date)
);

-- 4. 미국 주식 기본 정보 (Fundamentals)
CREATE TABLE IF NOT EXISTS joomoki_news.us_stock_fundamentals (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    base_date DATE NOT NULL,
    per DECIMAL(10,2),                      -- PER
    pbr DECIMAL(10,2),                      -- PBR
    eps DECIMAL(10,2),                      -- EPS
    roe DECIMAL(10,2),                      -- ROE
    div_yield DECIMAL(10,2),                -- 배당수익률
    market_cap BIGINT,                      -- 시가총액 (업데이트 시점)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES joomoki_news.us_stock_companies(stock_code),
    UNIQUE(stock_code, base_date)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_us_stock_companies_code ON joomoki_news.us_stock_companies(stock_code);
CREATE INDEX IF NOT EXISTS idx_us_stock_prices_code_date ON joomoki_news.us_stock_prices(stock_code, trade_date);
CREATE INDEX IF NOT EXISTS idx_us_stock_analysis_code_date ON joomoki_news.us_stock_analysis(stock_code, analysis_date);

-- 테이블 코멘트 (한글)
COMMENT ON TABLE joomoki_news.us_stock_companies IS '미국 주식 종목 정보';
COMMENT ON TABLE joomoki_news.us_stock_prices IS '미국 주식 일별 시세 데이터';
COMMENT ON TABLE joomoki_news.us_stock_analysis IS '미국 주식 AI 분석 결과';
COMMENT ON TABLE joomoki_news.us_stock_fundamentals IS '미국 주식 재무/기본 지표';

-- 컬럼 코멘트 (한글)
COMMENT ON COLUMN joomoki_news.us_stock_companies.stock_code IS '티커 심볼 (예: AAPL)';
COMMENT ON COLUMN joomoki_news.us_stock_companies.market_type IS '거래소 (NAS:나스닥, NYS:뉴욕, AMS:아멕스)';
COMMENT ON COLUMN joomoki_news.us_stock_companies.market_cap IS '시가총액 (USD)';

COMMENT ON COLUMN joomoki_news.us_stock_prices.trade_date IS '거래일자 (현지시간)';
COMMENT ON COLUMN joomoki_news.us_stock_prices.close_price IS '종가 (USD)';
COMMENT ON COLUMN joomoki_news.us_stock_prices.adj_close_price IS '수정주가';

COMMENT ON COLUMN joomoki_news.us_stock_analysis.summary IS 'AI 분석 요약 멘트';
COMMENT ON COLUMN joomoki_news.us_stock_analysis.price_prediction IS '향후 주가 예측 방향 (UP/DOWN/HOLD)';
