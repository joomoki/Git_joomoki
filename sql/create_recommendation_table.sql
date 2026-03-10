CREATE TABLE IF NOT EXISTS stock_recommendation_history (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    recommendation_date DATE NOT NULL,
    base_price DECIMAL(15, 2) NOT NULL,
    ai_score INT NOT NULL,
    is_us BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, recommendation_date)
);

CREATE INDEX IF NOT EXISTS idx_recommendation_date ON stock_recommendation_history(recommendation_date);
CREATE INDEX IF NOT EXISTS idx_stock_code_rec ON stock_recommendation_history(stock_code);
