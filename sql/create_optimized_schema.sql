-- DB 최적화를 위한 새로운 스키마 및 테이블 생성

-- 1. 국내 주식 마스터 (Master File 기반)
CREATE TABLE IF NOT EXISTS joomoki_news.stock_master (
    std_code VARCHAR(12) PRIMARY KEY,  -- 표준코드 (KR7...)
    short_code VARCHAR(10) NOT NULL,   -- 단축코드 (005930) - 실제 사용
    kor_name VARCHAR(100),             -- 한글명
    market_type VARCHAR(10),           -- KOSPI, KOSDAQ, KONEX 등
    sector_code VARCHAR(10),           -- 업종코드
    listing_date DATE,                 -- 상장일
    shares_outstanding BIGINT,         -- 상장주식수
    par_value INT,                     -- 액면가
    market_cap BIGINT,                 -- 시가총액 (계산값 또는 마스터 제공)
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stock_master_short_code ON joomoki_news.stock_master(short_code);

-- 2. 해외 주식 마스터
CREATE TABLE IF NOT EXISTS joomoki_news.global_stock_master (
    symbol VARCHAR(20) PRIMARY KEY,    -- 심볼 (AAPL)
    std_code VARCHAR(20),              -- 표준코드 (Optional)
    eng_name VARCHAR(100),             -- 영문명
    kor_name VARCHAR(100),             -- 한글명
    exchange_code VARCHAR(10),         -- NAS, NYS, AMS 등
    currency VARCHAR(5) DEFAULT 'USD', -- 통화
    sector VARCHAR(50),
    industry VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 통합 일별 시세 (Partitioned by Year)
-- 기존 stock_prices 구조를 개선하여 파티셔닝 적용
CREATE TABLE IF NOT EXISTS joomoki_news.daily_price (
    stock_code VARCHAR(20) NOT NULL,   -- 단축코드 또는 심볼
    trade_date DATE NOT NULL,
    open_price DECIMAL(15, 2),
    high_price DECIMAL(15, 2),
    low_price DECIMAL(15, 2),
    close_price DECIMAL(15, 2),
    volume BIGINT,
    amount BIGINT,                     -- 거래대금
    foreigner_exhaustion_rate DECIMAL(5, 2), -- 외국인 소진율
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (stock_code, trade_date)
) PARTITION BY RANGE (trade_date);

-- 파티션 테이블 생성 (2020 ~ 2030)
CREATE TABLE IF NOT EXISTS joomoki_news.daily_price_y2020 PARTITION OF joomoki_news.daily_price FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');
CREATE TABLE IF NOT EXISTS joomoki_news.daily_price_y2021 PARTITION OF joomoki_news.daily_price FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');
CREATE TABLE IF NOT EXISTS joomoki_news.daily_price_y2022 PARTITION OF joomoki_news.daily_price FOR VALUES FROM ('2022-01-01') TO ('2023-01-01');
CREATE TABLE IF NOT EXISTS joomoki_news.daily_price_y2023 PARTITION OF joomoki_news.daily_price FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE IF NOT EXISTS joomoki_news.daily_price_y2024 PARTITION OF joomoki_news.daily_price FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE IF NOT EXISTS joomoki_news.daily_price_y2025 PARTITION OF joomoki_news.daily_price FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE IF NOT EXISTS joomoki_news.daily_price_y2026 PARTITION OF joomoki_news.daily_price FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- 인덱스 (파티션별로 자동 적용되지만 명시적 확인)
-- 파티션 테이블은 Global Index를 지원하지 않으므로 각 파티션에 인덱스가 생성됨.
-- 여기서는 선언하지 않아도 PK가 있어서 기본 인덱스는 있음.
-- 조회 성능을 위해 날짜 인덱스 추가 (각 파티션에 전파됨)
CREATE INDEX ON joomoki_news.daily_price (trade_date);

-- 코멘트
COMMENT ON TABLE joomoki_news.stock_master IS '국내 주식 마스터 (KIS Master File)';
COMMENT ON TABLE joomoki_news.global_stock_master IS '해외 주식 마스터';
COMMENT ON TABLE joomoki_news.daily_price IS '통합 일별 시세 (Partitioned)';
