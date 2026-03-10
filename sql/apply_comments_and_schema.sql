-- 주식 종목 기본 정보 테이블 주석
COMMENT ON TABLE stock_companies IS '주식 종목 기본 정보 (코스피, 코스닥)';
COMMENT ON COLUMN stock_companies.stock_code IS '종목 코드 (6자리)';
COMMENT ON COLUMN stock_companies.company_name IS '종목명';
COMMENT ON COLUMN stock_companies.market_type IS '시장 구분 (KOSPI, KOSDAQ 등)';
COMMENT ON COLUMN stock_companies.sector IS '업종 (섹터)';
COMMENT ON COLUMN stock_companies.market_cap IS '시가총액 (원 단위)';
COMMENT ON COLUMN stock_companies.listed_date IS '상장일';
COMMENT ON COLUMN stock_companies.created_at IS '생성 일시';
COMMENT ON COLUMN stock_companies.updated_at IS '수정 일시';

-- 주식 일별 시세 테이블 주석
COMMENT ON TABLE stock_prices IS '주식 일별 시세 데이터 (OHLCV)';
COMMENT ON COLUMN stock_prices.id IS '고유 ID (Serial)';
COMMENT ON COLUMN stock_prices.stock_code IS '종목 코드';
COMMENT ON COLUMN stock_prices.trade_date IS '거래 일자';
COMMENT ON COLUMN stock_prices.open_price IS '시가';
COMMENT ON COLUMN stock_prices.high_price IS '고가';
COMMENT ON COLUMN stock_prices.low_price IS '저가';
COMMENT ON COLUMN stock_prices.close_price IS '종가';
COMMENT ON COLUMN stock_prices.volume IS '거래량';
COMMENT ON COLUMN stock_prices.market_cap IS '일별 시가총액 (원 단위)';
COMMENT ON COLUMN stock_prices.created_at IS '생성 일시';

-- 주식 기본적 분석 지표 (재무) 테이블 확장 및 주석
ALTER TABLE stock_fundamentals ADD COLUMN IF NOT EXISTS sales BIGINT;
ALTER TABLE stock_fundamentals ADD COLUMN IF NOT EXISTS operating_profit BIGINT;
ALTER TABLE stock_fundamentals ADD COLUMN IF NOT EXISTS total_assets BIGINT;
ALTER TABLE stock_fundamentals ADD COLUMN IF NOT EXISTS total_liabilities BIGINT;
ALTER TABLE stock_fundamentals ADD COLUMN IF NOT EXISTS debt_ratio FLOAT;

COMMENT ON TABLE stock_fundamentals IS '주식 기본적 분석 지표 (PER, PBR 등)';
COMMENT ON COLUMN stock_fundamentals.id IS '고유 ID';
COMMENT ON COLUMN stock_fundamentals.stock_code IS '종목 코드';
COMMENT ON COLUMN stock_fundamentals.base_date IS '기준 일자';
COMMENT ON COLUMN stock_fundamentals.per IS '주가수익비율 (PER)';
COMMENT ON COLUMN stock_fundamentals.pbr IS '주가순자산비율 (PBR)';
COMMENT ON COLUMN stock_fundamentals.eps IS '주당순이익 (EPS)';
COMMENT ON COLUMN stock_fundamentals.bps IS '주당순자산 (BPS)';
COMMENT ON COLUMN stock_fundamentals.market_cap IS '시가총액';
COMMENT ON COLUMN stock_fundamentals.shares_outstanding IS '상장 주식 수';
COMMENT ON COLUMN stock_fundamentals.foreigner_net_buy IS '외국인 순매수 수량';
COMMENT ON COLUMN stock_fundamentals.program_net_buy IS '프로그램 순매수 수량';
COMMENT ON COLUMN stock_fundamentals.foreigner_exhaustion_rate IS '외국인 소진율';
COMMENT ON COLUMN stock_fundamentals.sales IS '매출액 (원)';
COMMENT ON COLUMN stock_fundamentals.operating_profit IS '영업이익 (원)';
COMMENT ON COLUMN stock_fundamentals.total_assets IS '자산총계';
COMMENT ON COLUMN stock_fundamentals.total_liabilities IS '부채총계';
COMMENT ON COLUMN stock_fundamentals.debt_ratio IS '부채비율 (%)';

-- 주식 분석 결과 테이블 주석
COMMENT ON TABLE stock_analysis IS 'AI 기반 주식 분석 결과';
COMMENT ON COLUMN stock_analysis.id IS '고유 ID';
COMMENT ON COLUMN stock_analysis.stock_code IS '종목 코드';
COMMENT ON COLUMN stock_analysis.analysis_date IS '분석 일자';
COMMENT ON COLUMN stock_analysis.price_prediction IS '가격 예측 (UP/DOWN/HOLD)';
COMMENT ON COLUMN stock_analysis.analysis_summary IS '분석 요약 텍스트';
COMMENT ON COLUMN stock_analysis.confidence_level IS '확신도 (0~1)';
COMMENT ON COLUMN stock_analysis.signals IS '포착된 매매 신호 (JSON)';
COMMENT ON COLUMN stock_analysis.created_at IS '생성 일시';

-- [NEW] 투자자별 매매동향 테이블 생성
CREATE TABLE IF NOT EXISTS stock_investor_trends (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL REFERENCES stock_companies(stock_code),
    trade_date DATE NOT NULL,
    personal_net_buy BIGINT, -- 개인 순매수 (수량)
    foreigner_net_buy BIGINT, -- 외국인 순매수 (수량)
    institutional_net_buy BIGINT, -- 기관 순매수 (수량)
    program_net_buy BIGINT, -- 프로그램 순매수 (수량)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, trade_date)
);

COMMENT ON TABLE stock_investor_trends IS '투자자별 일별 매매동향';
COMMENT ON COLUMN stock_investor_trends.stock_code IS '종목 코드';
COMMENT ON COLUMN stock_investor_trends.trade_date IS '거래 일자';
COMMENT ON COLUMN stock_investor_trends.personal_net_buy IS '개인 순매수 수량';
COMMENT ON COLUMN stock_investor_trends.foreigner_net_buy IS '외국인 순매수 수량';
COMMENT ON COLUMN stock_investor_trends.institutional_net_buy IS '기관 순매수 수량';
COMMENT ON COLUMN stock_investor_trends.program_net_buy IS '프로그램 순매수 수량';
