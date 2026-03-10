import psycopg2
from psycopg2.extras import execute_values
import sys
import os

# 상위 디렉토리 경로 추가 (config 모듈 import 위함)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME

class StockDBManager:
    def __init__(self):
        self.conn = None

    def connect(self):
        """데이터베이스 연결"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            print(f"DB 연결 실패: {e}")
            return False

    def disconnect(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()

    def get_last_price_date(self, stock_code):
        """
        해당 종목의 마지막 저장된 trade_date 조회
        없으면 None 반환
        """
        if not self.conn:
            return None
        
        try:
            with self.conn.cursor() as cur:
                sql = f"SELECT MAX(trade_date) FROM {SCHEMA_NAME}.stock_prices WHERE stock_code = %s"
                cur.execute(sql, (stock_code,))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"마지막 날짜 조회 실패 ({stock_code}): {e}")
            return None

    def get_last_fundamental_date(self, stock_code):
        """
        해당 종목의 마지막 저장된 fundamental base_date 조회
        없으면 None 반환
        """
        if not self.conn:
            return None
        
        try:
            with self.conn.cursor() as cur:
                sql = f"SELECT MAX(base_date) FROM {SCHEMA_NAME}.stock_fundamentals WHERE stock_code = %s"
                cur.execute(sql, (stock_code,))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"마지막 기본정보 날짜 조회 실패 ({stock_code}): {e}")
            return None

    def get_close_price(self, stock_code, trade_date):
        """
        특정 날짜의 종가 조회
        """
        if not self.conn:
            return None
            
        try:
            with self.conn.cursor() as cur:
                sql = f"SELECT close_price FROM {SCHEMA_NAME}.stock_prices WHERE stock_code = %s AND trade_date = %s"
                cur.execute(sql, (stock_code, trade_date))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"종가 조회 실패 ({stock_code}, {trade_date}): {e}")
            return None

    def insert_stock_company(self, company_info):
        """
        주식 종목 정보 저장
        company_info: {'stock_code': '...', 'company_name': '...', 'description': '...', ...}
        """
        if not self.conn:
            return False
            
        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.stock_companies 
                    (stock_code, company_name, market_type, sector, market_cap, listed_date, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (stock_code) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    market_type = EXCLUDED.market_type,
                    sector = EXCLUDED.sector,
                    market_cap = EXCLUDED.market_cap,
                    description = COALESCE(EXCLUDED.description, {SCHEMA_NAME}.stock_companies.description),
                    updated_at = CURRENT_TIMESTAMP
                """
                cur.execute(sql, (
                    company_info['stock_code'],
                    company_info['company_name'],
                    company_info.get('market_type'),
                    company_info.get('sector'),
                    company_info.get('market_cap'),
                    company_info.get('listed_date'),
                    company_info.get('description')
                ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"종목 정보 저장 실패 ({company_info.get('stock_code')}): {e}")
            self.conn.rollback()
            return False

    def update_company_description(self, stock_code, description, is_us=False):
        """
        종목 설명(기업 개요) 업데이트 - 개별 업데이트용
        """
        if not self.conn:
            return False
            
        try:
            table = "us_stock_companies" if is_us else "stock_companies"
            with self.conn.cursor() as cur:
                sql = f"UPDATE {SCHEMA_NAME}.{table} SET description = %s, updated_at = CURRENT_TIMESTAMP WHERE stock_code = %s"
                cur.execute(sql, (description, stock_code))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"종목 설명 업데이트 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return False

    def get_all_stocks(self):
        """저장된 모든 종목 코드와 시장 구분 조회"""
        if not self.conn:
            return []
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"SELECT stock_code, market_type, company_name FROM {SCHEMA_NAME}.stock_companies")
                return cur.fetchall()
        except Exception as e:
            print(f"종목 목록 조회 실패: {e}")
            self.conn.rollback()
            return []

    def get_stocks_missing_description(self, is_us=False):
        """설명이 없는(NULL인) 종목 조회"""
        if not self.conn:
            return []
        try:
            table = "us_stock_companies" if is_us else "stock_companies"
            with self.conn.cursor() as cur:
                sql = f"SELECT stock_code, market_type, company_name FROM {SCHEMA_NAME}.{table} WHERE description IS NULL OR description = ''"
                cur.execute(sql)
                return cur.fetchall()
        except Exception as e:
            print(f"설명 미보유 종목 조회 실패: {e}")
            self.conn.rollback()
            return []

    def save_analysis_result(self, stock_code, analysis_data):
        """
        분석 결과 저장
        analysis_data: {
            'date': 'YYYY-MM-DD',
            'summary': '강력 매수',
            'score': 2,
            'confidence': 0.8
        }
        """
        if not self.conn:
            return False
            
        try:
            with self.conn.cursor() as cur:
                # 테이블 스키마에 맞춰 값 저장
                # prediction (UP/DOWN/HOLD) 매핑
                score = analysis_data.get('score', 0)
                if score >= 1: prediction = 'UP'
                elif score <= -1: prediction = 'DOWN'
                else: prediction = 'HOLD'
                
                if not isinstance(analysis_data.get('signals'), list):
                    signals_json = '[]'
                else:
                    import json
                    signals_json = json.dumps(analysis_data['signals'], ensure_ascii=False)

                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.stock_analysis 
                    (stock_code, analysis_date, price_prediction, analysis_summary, confidence_level, signals)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (stock_code, analysis_date) DO UPDATE SET
                    price_prediction = EXCLUDED.price_prediction,
                    analysis_summary = EXCLUDED.analysis_summary,
                    confidence_level = EXCLUDED.confidence_level,
                    signals = EXCLUDED.signals,
                    created_at = CURRENT_TIMESTAMP
                """
                cur.execute(sql, (
                    stock_code,
                    analysis_data['date'],
                    prediction,
                    analysis_data['summary'],
                    analysis_data.get('confidence', 0.0),
                    signals_json
                ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"분석 결과 저장 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return False

    def get_market_overview(self, date=None):
        """
        시장 전체 분석 현황 조회 (리스트 뷰용)
        """
        if not self.conn:
            return []
            
        try:
            if not date:
                from datetime import datetime
                date = datetime.now().strftime('%Y-%m-%d')

            with self.conn.cursor() as cur:
                # 최신 가격 정보와 분석 결과를 조인
                # 분석 결과가 없어도 회사 정보는 나오게 LEFT JOIN
                sql = f"""
                    SELECT 
                        c.stock_code, 
                        c.company_name, 
                        c.market_type,
                        c.sector,
                        p.close_price, 
                        p.volume,
                        a.analysis_summary,
                        a.price_prediction,
                        f.per,
                        f.pbr,
                        f.market_cap,
                        f.eps,
                        f.bps
                    FROM {SCHEMA_NAME}.stock_companies c
                    LEFT JOIN {SCHEMA_NAME}.stock_prices p ON c.stock_code = p.stock_code 
                        AND p.trade_date = (SELECT MAX(trade_date) FROM {SCHEMA_NAME}.stock_prices WHERE stock_code = c.stock_code)
                    LEFT JOIN {SCHEMA_NAME}.stock_analysis a ON c.stock_code = a.stock_code 
                        AND a.analysis_date = (SELECT MAX(analysis_date) FROM {SCHEMA_NAME}.stock_analysis WHERE stock_code = c.stock_code)
                    LEFT JOIN {SCHEMA_NAME}.stock_fundamentals f ON c.stock_code = f.stock_code
                        AND f.base_date = (SELECT MAX(base_date) FROM {SCHEMA_NAME}.stock_fundamentals WHERE stock_code = c.stock_code)
                    WHERE p.close_price IS NOT NULL
                    ORDER BY 
                        CASE 
                            WHEN a.price_prediction = 'UP' THEN 1 
                            WHEN a.price_prediction = 'DOWN' THEN 3
                            ELSE 2 
                        END,
                        c.market_cap DESC
                    LIMIT 100
                """
                
                cur.execute(sql)
                return cur.fetchall()
        except Exception as e:
            print(f"시장 현황 조회 실패: {e}")
            self.conn.rollback()
            return []

    def get_stock_info(self, stock_code):
        """
        단일 종목 정보 조회
        """
        if not self.conn:
            return None
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"SELECT stock_code, market_type, company_name FROM {SCHEMA_NAME}.stock_companies WHERE stock_code = %s", (stock_code,))
                result = cur.fetchone()
                return result # (code, market, name)
        except Exception as e:
            print(f"종목 정보 조회 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return None

    def get_filtered_stocks(self, criteria):
        """
        조건에 맞는 종목 필터링
        criteria: {
            'min_per': float, 'max_per': float,
            'min_pbr': float, 'max_pbr': float,
            'min_market_cap': int (억원 단위),
            'trend': 'UP'/'DOWN'/None
        }
        """
        if not self.conn:
            return []
            
        try:
            params = []
            conditions = ["p.close_price IS NOT NULL"] # 기본 조건: 현재가가 있어야 함

            if criteria.get('min_per'):
                conditions.append("f.per >= %s")
                params.append(criteria['min_per'])
            
            if criteria.get('max_per'):
                conditions.append("f.per <= %s")
                params.append(criteria['max_per'])
                
            if criteria.get('min_pbr'):
                conditions.append("f.pbr >= %s")
                params.append(criteria['min_pbr'])
                
            if criteria.get('max_pbr'):
                conditions.append("f.pbr <= %s")
                params.append(criteria['max_pbr'])

            if criteria.get('min_market_cap'):
                # 입력은 억 단위라고 가정, DB는 원 단위
                conditions.append("f.market_cap >= %s")
                params.append(criteria['min_market_cap'] * 100000000)

            if criteria.get('trend'):
                conditions.append("a.price_prediction = %s")
                params.append(criteria['trend'])

            where_clause = " AND ".join(conditions)

            with self.conn.cursor() as cur:
                sql = f"""
                    SELECT 
                        c.stock_code, 
                        c.company_name, 
                        c.market_type,
                        c.sector,
                        p.close_price, 
                        p.volume,
                        a.analysis_summary,
                        a.price_prediction,
                        f.per,
                        f.pbr,
                        f.market_cap,
                        a.signals
                    FROM {SCHEMA_NAME}.stock_companies c
                    LEFT JOIN {SCHEMA_NAME}.stock_prices p ON c.stock_code = p.stock_code 
                        AND p.trade_date = (SELECT MAX(trade_date) FROM {SCHEMA_NAME}.stock_prices WHERE stock_code = c.stock_code)
                    LEFT JOIN {SCHEMA_NAME}.stock_analysis a ON c.stock_code = a.stock_code 
                        AND a.analysis_date = (SELECT MAX(analysis_date) FROM {SCHEMA_NAME}.stock_analysis WHERE stock_code = c.stock_code)
                    LEFT JOIN {SCHEMA_NAME}.stock_fundamentals f ON c.stock_code = f.stock_code
                        AND f.base_date = (SELECT MAX(base_date) FROM {SCHEMA_NAME}.stock_fundamentals WHERE stock_code = c.stock_code)
                    WHERE {where_clause}
                    ORDER BY c.market_cap DESC
                """ # Removed LIMIT 100
                cur.execute(sql, tuple(params))
                return cur.fetchall()
        except Exception as e:
            print(f"종목 필터링 실패: {e}")
            return []

    def get_market_stocks(self, page=1, limit=30, market_type='ALL', sort_by='market_cap', target_date=None):
        """
        시장 목록 조회 (페이징, 마켓 필터, 정렬, 스파크라인 데이터 포함)
        """
        if not self.conn:
            return []
            
        try:
            if limit is None:
                offset = 0
            else:
                offset = (page - 1) * limit
            
            params = []
            conditions = ["p.close_price IS NOT NULL"] # 상장폐지 등 데이터 없는 종목 제외

            if market_type != 'ALL':
                conditions.append("c.market_type = %s")
                params.append(market_type)

            where_clause = " AND ".join(conditions)

            # 정렬 기준 매핑
            order_clause = "c.market_cap DESC NULLS LAST" # 기본값
            if sort_by == 'market_cap':
                order_clause = "c.market_cap DESC NULLS LAST"
            elif sort_by == 'per':
                # PER는 낮을수록 좋음 (단, 0보다 큰 경우) -> 오름차순
                # NULL이나 음수, 0 처리가 복잡할 수 있음. 일단 단순 오름차순
                order_clause = "f.per ASC NULLS LAST"
            elif sort_by == 'pbr':
                 order_clause = "f.pbr ASC NULLS LAST"
            elif sort_by == 'volume':
                order_clause = "p.volume DESC NULLS LAST"
            elif sort_by == 'change':
                # 등락률은 현재 테이블에 없으므로 (전일 대비 계산 필요)
                # 일단은 구현 보류하거나, 급등주 등 별도 로직 필요.
                # 여기서는 'prediction' (UP 우선) 등으로 대체 가능
                order_clause = "CASE WHEN a.price_prediction = 'UP' THEN 1 WHEN a.price_prediction = 'DOWN' THEN 3 ELSE 2 END, c.market_cap DESC"
            elif sort_by == 'prediction':
                # 매수(UP) > 중립(HOLD, NULL) > 매도(DOWN) 순 정렬
                order_clause = """
                    CASE 
                        WHEN a.price_prediction = 'UP' THEN 1 
                        WHEN a.price_prediction = 'HOLD' OR a.price_prediction IS NULL THEN 2
                        WHEN a.price_prediction = 'DOWN' THEN 3 
                        ELSE 4
                    END ASC, 
                    c.market_cap DESC NULLS LAST
                """

            with self.conn.cursor() as cur:
                # [MODIFIED] daily_price + stock_prices 병합하여 최신 데이터 조회
                # price_history 서브쿼리에서도 병합된 데이터 사용
                
                sql = f"""
                    SELECT 
                        c.stock_code, 
                        c.company_name, 
                        c.market_type,
                        c.sector,
                        p.close_price, 
                        p.volume,
                        p.trade_date, --- 기준일
                        a.analysis_summary,
                        a.price_prediction,
                        f.per,
                        f.pbr,
                        f.market_cap,
                        f.eps,
                        f.bps,
                        f.sales,
                        f.operating_profit,
                        f.debt_ratio,
                        f.foreigner_net_buy,
                        f.program_net_buy,
                        a.confidence_level,
                        a.signals,
                        a.ai_score,
                        (
                            SELECT json_agg(json_build_object(
                                'date', to_char(trade_date, 'YYYY-MM-DD'),
                                'open', open_price,
                                'high', high_price,
                                'low', low_price,
                                'close', close_price,
                                'volume', volume
                            ) ORDER BY trade_date ASC)
                            FROM (
                                SELECT trade_date, open_price, high_price, low_price, close_price, volume
                                FROM (
                                    SELECT trade_date, open_price, high_price, low_price, close_price, volume, stock_code
                                    FROM {SCHEMA_NAME}.daily_price
                                    UNION ALL
                                    SELECT trade_date, open_price, high_price, low_price, close_price, volume, stock_code
                                    FROM {SCHEMA_NAME}.stock_prices
                                ) sp_union
                                WHERE sp_union.stock_code = c.stock_code 
                                {'AND sp_union.trade_date <= %s' if target_date else ''}
                                ORDER BY trade_date DESC 
                                LIMIT 120
                            ) sub
                        ) as price_history,
                        (
                            SELECT ARRAY_AGG(foreigner_net_buy ORDER BY trade_date ASC)
                            FROM (
                                SELECT foreigner_net_buy, trade_date 
                                FROM {SCHEMA_NAME}.stock_investor_trends it 
                                WHERE it.stock_code = c.stock_code 
                                {'AND it.trade_date <= %s' if target_date else ''}
                                ORDER BY trade_date DESC 
                                LIMIT 20
                            ) sub_f
                        ) as foreigner_trend,
                        (
                            SELECT ARRAY_AGG(institutional_net_buy ORDER BY trade_date ASC)
                            FROM (
                                SELECT institutional_net_buy, trade_date 
                                FROM {SCHEMA_NAME}.stock_investor_trends it 
                                WHERE it.stock_code = c.stock_code 
                                {'AND it.trade_date <= %s' if target_date else ''}
                                ORDER BY trade_date DESC 
                                LIMIT 20
                            ) sub_i
                        ) as institution_trend,
                        c.description,
                        -- [DB VIEW] 등락률: v_latest_price_with_change에서 직접 가져옴 (target_date 없을 때만)
                        {'vcr.change_rate' if not target_date else 'NULL::numeric'} AS change_rate
                    FROM {SCHEMA_NAME}.stock_companies c
                    LEFT JOIN (
                        SELECT stock_code, trade_date, close_price, volume 
                        FROM (
                            SELECT stock_code, trade_date, close_price, volume,
                                   ROW_NUMBER() OVER (PARTITION BY stock_code ORDER BY trade_date DESC) as rn
                            FROM (
                                SELECT stock_code, trade_date, close_price, volume FROM {SCHEMA_NAME}.daily_price
                                UNION ALL
                                SELECT stock_code, trade_date, close_price, volume FROM {SCHEMA_NAME}.stock_prices
                            ) u
                            WHERE 1=1
                            {'AND trade_date <= %s' if target_date else ''}
                        ) ranked
                        WHERE rn = 1
                    ) p ON c.stock_code = p.stock_code
                        AND p.trade_date = {'%s' if target_date else f"(SELECT MAX(trade_date) FROM (SELECT trade_date FROM {SCHEMA_NAME}.daily_price WHERE stock_code = c.stock_code UNION ALL SELECT trade_date FROM {SCHEMA_NAME}.stock_prices WHERE stock_code = c.stock_code) mx)"}
                    LEFT JOIN {SCHEMA_NAME}.stock_analysis a ON c.stock_code = a.stock_code 
                        AND a.analysis_date = {'%s' if target_date else f"(SELECT MAX(analysis_date) FROM {SCHEMA_NAME}.stock_analysis WHERE stock_code = c.stock_code)"}
                    LEFT JOIN {SCHEMA_NAME}.stock_fundamentals f ON c.stock_code = f.stock_code
                        AND f.base_date = (SELECT MAX(base_date) FROM {SCHEMA_NAME}.stock_fundamentals WHERE stock_code = c.stock_code)
                    {'LEFT JOIN ' + SCHEMA_NAME + '.v_latest_price_with_change vcr ON c.stock_code = vcr.stock_code' if not target_date else ''}
                    WHERE {where_clause}
                    ORDER BY {order_clause}
                    LIMIT {limit if limit else 'ALL'} OFFSET {offset}
                """
                
                # params 순서: 
                # 1. price_history subquery target_date (if exists)
                # 2. foreigner_trend subquery target_date (if exists)
                # 3. institution_trend subquery target_date (if exists)
                # 4. main query stock_prices join target_date (if exists) <- UNION subquery inside JOIN
                # 5. main query stock_analysis join target_date (if exists)
                # 6. market_type (if exists)
                
                query_params = []
                if target_date:
                    query_params.append(target_date) # 1. price_history subquery
                    query_params.append(target_date) # 2. foreigner_trend subquery
                    query_params.append(target_date) # 3. institution_trend subquery
                    query_params.append(target_date) # 4. p subquery filter (505)
                    query_params.append(target_date) # 5. p join condition (509)
                    query_params.append(target_date) # 6. stock_analysis join condition (511)
                
                query_params.extend(params)
                
                cur.execute(sql, tuple(query_params))
                return cur.fetchall()
        except Exception as e:
            print(f"시장 목록 조회 실패: {e}")
            self.conn.rollback()
            return []

    def update_ai_score(self, stock_code, score, analysis_date, is_us=False):
        """
        AI 점수 업데이트 (UPSERT)
        stock_analysis 테이블과 daily_price/us_stock_prices 테이블 모두 업데이트
        """
        if not self.conn:
            return False
            
        try:
            table_name = "us_stock_analysis" if is_us else "stock_analysis"
            price_table_name = "us_stock_prices" if is_us else "daily_price"
            
            # score 기준으로 prediction 파생 
            prediction = 'UP' if score >= 70 else ('DOWN' if score <= 30 else 'HOLD')
            
            with self.conn.cursor() as cur:
                # 1. Analysis 테이블 업데이트
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.{table_name} (stock_code, analysis_date, ai_score, price_prediction)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (stock_code, analysis_date) 
                    DO UPDATE SET ai_score = EXCLUDED.ai_score,
                                  price_prediction = EXCLUDED.price_prediction,
                                  updated_at = CURRENT_TIMESTAMP
                """
                cur.execute(sql, (stock_code, analysis_date, score, prediction))
                
                # 2. Price 테이블 업데이트 (ai_score 컬럼 추가됨)
                # 해당 날짜의 가격 데이터가 존재할 경우에만 업데이트
                sql_price = f"""
                    UPDATE {SCHEMA_NAME}.{price_table_name}
                    SET ai_score = %s
                    WHERE stock_code = %s AND trade_date = %s
                """
                cur.execute(sql_price, (score, stock_code, analysis_date))
                
            self.conn.commit()
            return True
        except Exception as e:
            print(f"AI 점수 업데이트 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return False

    def get_market_stock_count(self, market_type='ALL'):
        """
        시장 목록 전체 개수 조회 (페이징용)
        """
        if not self.conn:
            return 0
        try:
            params = []
            conditions = ["p.close_price IS NOT NULL"]

            if market_type != 'ALL':
                conditions.append("c.market_type = %s")
                params.append(market_type)

            where_clause = " AND ".join(conditions)
            
            with self.conn.cursor() as cur:
                sql = f"""
                    SELECT COUNT(*)
                    FROM {SCHEMA_NAME}.stock_companies c
                    LEFT JOIN {SCHEMA_NAME}.stock_prices p ON c.stock_code = p.stock_code 
                        AND p.trade_date = (SELECT MAX(trade_date) FROM {SCHEMA_NAME}.stock_prices WHERE stock_code = c.stock_code)
                    WHERE {where_clause}
                """
                cur.execute(sql, tuple(params))
                result = cur.fetchone()
                return result[0] if result else 0
        except Exception as e:
            print(f"시장 목록 개수 조회 실패: {e}")
            self.conn.rollback()
            return 0

    def save_daily_fundamentals(self, stock_code, data, date=None):
        """
        주식 기본 정보 저장 (stock_fundamentals)
        data: get_current_price_detailed의 리턴값 (output 딕셔너리)
        """
        if not self.conn or not data:
            return False
            
        try:
            if not date:
                from datetime import datetime
                date = datetime.now().strftime('%Y-%m-%d')

            with self.conn.cursor() as cur:
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.stock_fundamentals
                    (stock_code, base_date, per, pbr, eps, bps, market_cap, 
                    (stock_code, base_date, per, pbr, eps, bps, market_cap, 
                     shares_outstanding, foreigner_net_buy, program_net_buy, 
                     foreigner_exhaustion_rate, sales, operating_profit, total_assets, total_liabilities, debt_ratio)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (stock_code, base_date) DO UPDATE SET
                    per = EXCLUDED.per,
                    pbr = EXCLUDED.pbr,
                    eps = EXCLUDED.eps,
                    bps = EXCLUDED.bps,
                    market_cap = EXCLUDED.market_cap,
                    shares_outstanding = EXCLUDED.shares_outstanding,
                    foreigner_net_buy = EXCLUDED.foreigner_net_buy,
                    program_net_buy = EXCLUDED.program_net_buy,
                    foreigner_exhaustion_rate = EXCLUDED.foreigner_exhaustion_rate,
                    sales = EXCLUDED.sales,
                    operating_profit = EXCLUDED.operating_profit,
                    total_assets = EXCLUDED.total_assets,
                    total_liabilities = EXCLUDED.total_liabilities,
                    debt_ratio = EXCLUDED.debt_ratio,
                    created_at = CURRENT_TIMESTAMP
                """
                
                # 데이터 파싱 (API 응답 필드명 매핑)
                def to_float(val):
                    try: return float(val.replace(',', '')) if val else None
                    except: return None
                
                def to_int(val):
                    try: return int(val.replace(',', '')) if val else None
                    except: return None

                # 시가총액: API에서 억 단위로 줄 수도 있고 원 단위일 수도 있음. 
                # hts_avls(시가총액/억)
                market_cap = to_int(data.get('hts_avls', '0'))
                if market_cap: market_cap *= 100000000 

                cur.execute(sql, (
                    stock_code,
                    date,
                    to_float(data.get('per')),
                    to_float(data.get('pbr')),
                    to_float(data.get('eps')),
                    to_float(data.get('bps')),
                    market_cap,
                    to_int(data.get('lstn_stcn')), # 상장주식수
                    to_int(data.get('frgn_ntby_qty')), # 외국인
                    to_int(data.get('pgtr_ntby_qty')), # 프로그램
                    to_float(data.get('hts_frgn_ehrt')), # 소진율
                    to_int(data.get('acml_tr_pbmn')), # 누적거래대금(임시 매핑, 매출액 아님. API 필드 확인 필요)
                    # 현재 inquire-price API(FHKST01010100)는 매출/영업이익을 안 줌.
                    # 일단 NULL로 처리하거나 추후 inquire-finance API 등으로 보완 필요.
                    None, # operating_profit
                    None, # total_assets
                    None, # total_liabilities
                    None  # debt_ratio
                ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"기본 정보 저장 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return False

    def insert_price_list(self, stock_code, price_data_tuples):
        """
        정제된 시세 데이터 대량 저장
        price_data_tuples: [(trade_date(str/date), open, high, low, close, volume, market_cap), ...]
        """
        if not self.conn or not price_data_tuples:
            return False

        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.stock_prices 
                    (stock_code, trade_date, open_price, high_price, low_price, close_price, volume, market_cap)
                    VALUES %s
                    ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume,
                    market_cap = EXCLUDED.market_cap
                """
                # stock_code를 각 튜플 앞에 추가해야 함
                # 입력받은 튜플 구조에 따라 다름. 여기서는 입력 튜플이 (trade_date, ...) 라고 가정하고
                # execute_values를 위해 (stock_code, trade_date, ...) 형태로 변환하거나
                # 호출측에서 맞춰주길 기대함.
                # 편의를 위해 호출측에서 (trade_date, o, h, l, c, v, cap) 만 넘기면 여기서 stock_code 붙여줌
                
                final_data = []
                for row in price_data_tuples:
                    # row: (trade_date, open, high, low, close, volume, market_cap)
                    final_data.append((stock_code,) + row)

                execute_values(cur, sql, final_data)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"시세 저장 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return False

    def insert_daily_prices(self, stock_code, price_data_list):
        """
        일별 시세 데이터 대량 저장
        price_data_list: [{'stck_bsop_date': '20240101', 'stck_oprc': '...', ...}, ...]
        API 응답 포맷(output2)을 그대로 받아서 처리
        """
        if not self.conn:
            return False
            
        data_to_insert = []
        for data in price_data_list:
            # 주말/휴일 등으로 데이터가 비어있거나 0인 경우 처리 필요할 수 있음
            # API 응답 키 매핑
            trade_date = data['stck_bsop_date']
            # YYYYMMDD -> YYYY-MM-DD (Postgres DATE 타입 호환)
            formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
            
            row = (
                stock_code,
                formatted_date,
                float(data['stck_oprc']), # 시가
                float(data['stck_hgpr']), # 고가
                float(data['stck_lwpr']), # 저가
                float(data['stck_clpr']), # 종가
                int(data['acml_vol']),    # 거래량
                # market_cap 정보는 일별 시세 API 응답(output2)에는 없을 수 있음. 
                # 현재가 조회(output) 등 다른 API나 계산이 필요하나 일단 NULL 허용이면 생략
            )
            data_to_insert.append(row)

        if not data_to_insert:
            return False

        try:
            with self.conn.cursor() as cur:
                # upsert 쿼리
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.stock_prices 
                    (stock_code, trade_date, open_price, high_price, low_price, close_price, volume)
                    VALUES %s
                    ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume
                """
                execute_values(cur, sql, data_to_insert)
            self.conn.commit()
            print(f"{len(data_to_insert)}건의 시세 데이터 저장 완료 ({stock_code})")
            return True
        except Exception as e:
            print(f"시세 데이터 저장 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return False

    def search_stocks(self, query):
        """
        종목 검색 (이름 또는 코드)
        """
        if not self.conn:
            return []
            
        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    SELECT stock_code, market_type, company_name 
                    FROM {SCHEMA_NAME}.stock_companies 
                    WHERE stock_code LIKE %s OR company_name LIKE %s
                    LIMIT 20
                """
                like_query = f"%{query}%"
                cur.execute(sql, (like_query, like_query))
                return cur.fetchall()
        except Exception as e:
            print(f"종목 검색 실패: {e}")
            self.conn.rollback()
            return []

    def get_daily_prices_after(self, stock_code, start_date, is_us=False):
        """
        특정 날짜 이후의 일별 시세 조회 (수익률 추적용)
        Returns: [(date, close_price), ...]
        """
        if not self.conn:
            return []
            
        try:
            with self.conn.cursor() as cur:
                if is_us:
                    sql = f"""
                        SELECT trade_date, close_price
                        FROM {SCHEMA_NAME}.us_stock_prices
                        WHERE stock_code = %s AND trade_date > %s
                        ORDER BY trade_date ASC
                        LIMIT 10
                    """
                    cur.execute(sql, (stock_code, start_date))
                    return cur.fetchall()
                else:
                    sql = f"""
                        SELECT trade_date, close_price
                        FROM (
                            SELECT trade_date, close_price FROM {SCHEMA_NAME}.daily_price
                            WHERE stock_code = %s AND trade_date > %s
                            UNION ALL
                            SELECT trade_date, close_price FROM {SCHEMA_NAME}.stock_prices
                            WHERE stock_code = %s AND trade_date > %s
                        ) u
                        ORDER BY trade_date ASC
                        LIMIT 10
                    """
                    cur.execute(sql, (stock_code, start_date, stock_code, start_date))
                    return cur.fetchall()
        except Exception as e:
            print(f"일별 시세 조회 실패 ({stock_code}): {e}")
            return []

    def get_daily_prices(self, stock_code, limit=365):
        """
        특정 종목의 일별 시세 조회
        """
        if not self.conn:
            return []
            
        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    SELECT trade_date, open_price, high_price, low_price, close_price, volume 
                    FROM {SCHEMA_NAME}.stock_prices 
                    WHERE stock_code = %s 
                    ORDER BY trade_date ASC
                    LIMIT %s
                """
                # LIMIT는 최근 데이터 기준이 아니라 전체 데이터 중 날짜 오름차순으로 가져오면 
                # 옛날 데이터만 가져올 수 있음. 
                # 보통 최근 1년치 등을 원하므로, 날짜 조건을 추가하거나 정렬을 신경써야 함.
                # 여기서는 간단히 전체 중 최근 limit개? 아니면 그냥 1년치?
                # 사용처가 차트/분석이므로 '최근' 데이터가 중요.
                # -> 날짜 내림차순으로 limit개 가져와서 다시 오름차순 정렬하는게 일반적.
                
                sql = f"""
                    SELECT * FROM (
                        SELECT trade_date, open_price, high_price, low_price, close_price, volume 
                        FROM {SCHEMA_NAME}.stock_prices 
                        WHERE stock_code = %s 
                        ORDER BY trade_date DESC
                        LIMIT %s
                    ) sub
                    ORDER BY trade_date ASC
                """
                cur.execute(sql, (stock_code, limit))
                return cur.fetchall()
        except Exception as e:
            print(f"일별 시세 조회 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return []
    def delete_recommendation_history(self, date):
        """
        특정 날짜의 추천 이력 삭제 (중복/불일치 방지용)
        date: 'YYYY-MM-DD' 문자열 또는 date 객체
        """
        if not self.conn:
            return False
            
        try:
            with self.conn.cursor() as cur:
                sql = f"DELETE FROM {SCHEMA_NAME}.stock_recommendation_history WHERE recommendation_date = %s"
                cur.execute(sql, (date,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"추천 이력 삭제 실패 ({date}): {e}")
            self.conn.rollback()
            return False

    def save_recommendation_history(self, stock_code, date, price, score, is_us=False):
        """
        AI 추천 종목 이력 저장
        """
        if not self.conn:
            return False
            
        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.stock_recommendation_history
                    (stock_code, recommendation_date, base_price, ai_score, is_us)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (stock_code, recommendation_date) 
                    DO UPDATE SET base_price = EXCLUDED.base_price, 
                                  ai_score = EXCLUDED.ai_score
                """
                cur.execute(sql, (stock_code, date, price, score, is_us))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"추천 이력 저장 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return False

    def get_recommendation_history_with_performance(self):
        """
        추천 이력과 현재 성과 조회
        """
        if not self.conn:
            return []
            
        try:
            with self.conn.cursor() as cur:
                # 최신 가격 조인을 위한 서브쿼리 활용 (daily_price + stock_prices)
                
                sql = f"""
                    WITH latest_prices AS (
            SELECT stock_code, close_price
            FROM (
                SELECT stock_code, close_price, ROW_NUMBER() OVER (PARTITION BY stock_code ORDER BY trade_date DESC) as rn
                FROM (
                    SELECT stock_code, close_price, trade_date
                    FROM {SCHEMA_NAME}.daily_price
                    UNION ALL
                    SELECT stock_code, close_price, trade_date
                    FROM {SCHEMA_NAME}.stock_prices
                ) all_p
            ) u
            WHERE rn = 1
        ),
                    latest_us_prices AS (
                        SELECT stock_code, close_price
                        FROM {SCHEMA_NAME}.us_stock_prices
                        WHERE (stock_code, trade_date) IN (
                            SELECT stock_code, MAX(trade_date)
                            FROM {SCHEMA_NAME}.us_stock_prices
                            GROUP BY stock_code
                        )
                    )
                    SELECT 
                        h.recommendation_date,
                        h.stock_code,
                        CASE 
                            WHEN h.is_us THEN COALESCE(uc.korean_name, uc.company_name)
                            ELSE c.company_name 
                        END as company_name,
                        CASE 
                            WHEN h.is_us THEN uc.market_type 
                            ELSE c.market_type 
                        END as market_type,
                        h.base_price, -- 추천 당시 가격
                        CASE 
                            WHEN h.is_us THEN up.close_price
                            ELSE p.close_price
                        END as close_price, -- 현재 가격 (최신)
                        CASE
                            WHEN h.is_us THEN ((up.close_price - h.base_price) / h.base_price * 100)
                            ELSE ((p.close_price - h.base_price) / h.base_price * 100)
                        END as return_rate,
                        h.ai_score,
                        h.is_us
                    FROM {SCHEMA_NAME}.stock_recommendation_history h
                    LEFT JOIN {SCHEMA_NAME}.stock_companies c ON h.stock_code = c.stock_code AND h.is_us = FALSE
                    LEFT JOIN {SCHEMA_NAME}.us_stock_companies uc ON h.stock_code = uc.stock_code AND h.is_us = TRUE
                    LEFT JOIN latest_prices p ON h.stock_code = p.stock_code AND h.is_us = FALSE
                    LEFT JOIN latest_us_prices up ON h.stock_code = up.stock_code AND h.is_us = TRUE
                    ORDER BY h.recommendation_date DESC, h.ai_score DESC
                """
                cur.execute(sql)
                return cur.fetchall()
        except Exception as e:
            print(f"추천 이력 조회 실패: {e}")
            self.conn.rollback()
            return []

    def insert_investor_trend(self, stock_code, trend_data_list):
        """
        투자자별 매매동향 저장
        trend_data_list: get_investor_trend의 리턴값 (output 리스트)
        """
        if not self.conn or not trend_data_list:
            return False
            
        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.stock_investor_trends
                    (stock_code, trade_date, personal_net_buy, foreigner_net_buy, institutional_net_buy, program_net_buy)
                    VALUES %s
                    ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                    personal_net_buy = EXCLUDED.personal_net_buy,
                    foreigner_net_buy = EXCLUDED.foreigner_net_buy,
                    institutional_net_buy = EXCLUDED.institutional_net_buy,
                    program_net_buy = EXCLUDED.program_net_buy
                """
                
                data_to_insert = []
                for d in trend_data_list:
                    # 날짜 포맷 확인: YYYYMMDD -> YYYY-MM-DD
                    raw_date = d.get('stck_bsop_date')
                    if not raw_date: continue
                    date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
                    
                    data_to_insert.append((
                        stock_code,
                        date_str,
                        int(d.get('prsn_ntby_qty', 0) or 0),
                        int(d.get('frgn_ntby_qty', 0) or 0),
                        int(d.get('orgn_ntby_qty', 0) or 0),
                        int(d.get('pgtr_ntby_qty', 0) or 0) # 프로그램은 없을 수도 있음
                    ))
                
                if data_to_insert:
                    execute_values(cur, sql, data_to_insert)
                    self.conn.commit()
                    return True
                return False
                
        except Exception as e:
            print(f"투자자 동향 저장 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return False

    # ==========================================
    # 미국 주식 관련 메서드 추가
    # ==========================================

    def insert_us_stock_company(self, company_info):
        """
        미국 주식 종목 정보 저장
        company_info: {'stock_code': 'AAPL', 'company_name': 'Apple Inc', 'korean_name': '애플', ...}
        """
        if not self.conn:
            return False
            
        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.us_stock_companies 
                    (stock_code, company_name, korean_name, market_type, sector, industry, market_cap)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (stock_code) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    korean_name = EXCLUDED.korean_name,
                    market_type = EXCLUDED.market_type,
                    sector = EXCLUDED.sector,
                    industry = EXCLUDED.industry,
                    market_cap = EXCLUDED.market_cap,
                    updated_at = CURRENT_TIMESTAMP
                """
                cur.execute(sql, (
                    company_info['stock_code'],
                    company_info['company_name'],
                    company_info.get('korean_name'),
                    company_info.get('market_type'),
                    company_info.get('sector'),
                    company_info.get('industry'),
                    company_info.get('market_cap')
                ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"미국 종목 정보 저장 실패 ({company_info.get('stock_code')}): {e}")
            self.conn.rollback()
            return False

    def insert_us_stock_prices(self, stock_code, price_data_list):
        """
        미국 주식 일별 시세 저장
        price_data_list: [{'date': '2025-01-01', 'open': 100.0, ...}, ...]
        """
        if not self.conn or not price_data_list:
            return False
            
        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.us_stock_prices 
                    (stock_code, trade_date, open_price, high_price, low_price, close_price, volume, adj_close_price)
                    VALUES %s
                    ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume,
                    adj_close_price = EXCLUDED.adj_close_price
                """
                
                final_data = []
                for p in price_data_list:
                    # 날짜 포맷 확인
                    trade_date = p.get('date') or p.get('stck_bsop_date') # API마다 다를 수 있음
                    if not trade_date: continue
                    
                    # YYYYMMDD -> YYYY-MM-DD
                    if len(str(trade_date)) == 8 and str(trade_date).isdigit():
                        trade_date = f"{str(trade_date)[:4]}-{str(trade_date)[4:6]}-{str(trade_date)[6:]}"

                    final_data.append((
                        stock_code,
                        trade_date,
                        p.get('open'),
                        p.get('high'),
                        p.get('low'),
                        p.get('close'),
                        p.get('volume'),
                        p.get('adj_close')
                    ))
                
                if final_data:
                    execute_values(cur, sql, final_data)
                    self.conn.commit()
                    return True
                return False
        except Exception as e:
            print(f"미국 시세 저장 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return False

    def save_us_analysis_result(self, stock_code, analysis_data):
        """
        미국 주식 분석 결과 저장
        """
        if not self.conn:
            return False
            
        try:
            with self.conn.cursor() as cur:
                # signals JSON 처리
                import json
                signals = analysis_data.get('signals', {})
                signals_json = json.dumps(signals) if signals else None

                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.us_stock_analysis 
                    (stock_code, analysis_date, summary, sentiment_score, price_prediction, confidence, signals)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (stock_code, analysis_date) DO UPDATE SET
                    summary = EXCLUDED.summary,
                    sentiment_score = EXCLUDED.sentiment_score,
                    price_prediction = EXCLUDED.price_prediction,
                    confidence = EXCLUDED.confidence,
                    signals = EXCLUDED.signals,
                    created_at = CURRENT_TIMESTAMP
                """
                cur.execute(sql, (
                    stock_code,
                    analysis_data['date'],
                    analysis_data.get('summary'),
                    analysis_data.get('sentiment_score'),
                    analysis_data.get('price_prediction'),
                    analysis_data.get('confidence'),
                    signals_json
                ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"미국 분석 저장 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return False
            
    def insert_us_stock_news(self, news_data_list):
        """
        미국 주식 뉴스 및 감성 분석 저장
        news_data_list: [{'stock_code': 'AAPL', 'title': '...', 'sentiment_score': 0.5, ...}, ...]
        """
        if not self.conn or not news_data_list:
            return False
            
        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.us_stock_news
                    (stock_code, news_date, title, link, source, sentiment_score, sentiment_label)
                    VALUES %s
                    ON CONFLICT (stock_code, title) DO NOTHING
                """
                
                final_data = []
                for n in news_data_list:
                    final_data.append((
                        n['stock_code'],
                        n['news_date'], # datetime object
                        n['title'],
                        n.get('link'),
                        n.get('source'),
                        n.get('sentiment_score'),
                        n.get('sentiment_label')
                    ))
                
                if final_data:
                    execute_values(cur, sql, final_data)
                    self.conn.commit()
                    return True
                return False
        except Exception as e:
            print(f"미국 뉴스 저장 실패: {e}")
            self.conn.rollback()
            return False

    def insert_us_stock_fundamentals(self, stock_code, data, date=None):
        """
        미국 주식 펀더멘털 데이터 저장
        data: KisApiClient.get_overseas_stock_info 응답 (per, eps, shar, last 등 포함)
        """
        if not self.conn or not data:
            return False
            
        try:
            if not date:
                from datetime import datetime
                date = datetime.now().strftime('%Y-%m-%d')
                
            with self.conn.cursor() as cur:
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.us_stock_fundamentals
                    (stock_code, base_date, per, eps, market_cap)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (stock_code, base_date) DO UPDATE SET
                    per = EXCLUDED.per,
                    eps = EXCLUDED.eps,
                    market_cap = EXCLUDED.market_cap,
                    created_at = CURRENT_TIMESTAMP
                """
                # 데이터 파싱
                # data = {'eps': '6.08', 'per': '41.91', 'shar': '150...', 'last': '254...'}
                def to_float(val):
                    try: return float(val.replace(',', '')) if val else None
                    except: return None
                
                per = to_float(data.get('per'))
                eps = to_float(data.get('eps'))
                
                # 시가총액 계산 (상장주식수 * 현재가)
                # shar: 상장주식수 (문자열일 수 있음)
                # last: 현재가
                market_cap = None
                try:
                    shar = float(data.get('shar', 0))
                    last = float(data.get('last', 0))
                    if shar > 0 and last > 0:
                        market_cap = int(shar * last)
                except:
                    pass
                
                cur.execute(sql, (
                    stock_code,
                    date,
                    per,
                    eps,
                    market_cap
                ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"미국 펀더멘털 저장 실패 ({stock_code}): {e}")
            self.conn.rollback()
            return False

    def get_us_market_stocks(self, limit=None, sort_by='market_cap', target_date=None):
        """
        미국 주식 시장 현황 조회 (모바일 웹 표시용)
        """
        if not self.conn:
            return []
            
        try:
            with self.conn.cursor() as cur:
                # 정렬 기준
                if sort_by == 'prediction':
                    order_clause = """
                        CASE 
                            WHEN a.price_prediction = 'UP' THEN 1 
                            WHEN a.price_prediction = 'HOLD' OR a.price_prediction IS NULL THEN 2
                            WHEN a.price_prediction = 'DOWN' THEN 3 
                            ELSE 4
                        END ASC, 
                        c.market_cap DESC NULLS LAST
                    """
                else:
                    order_clause = "c.market_cap DESC NULLS LAST"

                # 펀더멘털 정보도 조인해서 가져옴
                # price_history: OHLC 데이터 json_agg로 변경
                sql = f"""
                    SELECT 
                        c.stock_code, 
                        c.company_name, 
                        c.korean_name,
                        c.market_type,
                        c.sector,
                        p.close_price, 
                        p.volume,
                        p.trade_date,
                        a.summary,
                        a.price_prediction,
                        a.sentiment_score,
                        a.confidence,
                        a.ai_score, -- 추가
                        c.market_cap,
                        (
                            SELECT json_agg(json_build_object(
                                'date', to_char(trade_date, 'YYYY-MM-DD'),
                                'open', open_price,
                                'high', high_price,
                                'low', low_price,
                                'close', close_price,
                                'volume', volume
                            ) ORDER BY trade_date ASC)
                            FROM (
                                SELECT trade_date, open_price, high_price, low_price, close_price, volume
                                FROM {SCHEMA_NAME}.us_stock_prices sp 
                                WHERE sp.stock_code = c.stock_code 
                                {'AND sp.trade_date <= %s' if target_date else ''}
                                ORDER BY trade_date DESC 
                                LIMIT 120
                            ) sub
                        ) as price_history,
                        f.per,
                        f.eps,
                        f.pbr,   -- 현재 수집 안됨 (구조상 컬럼은 있음)
                        f.roe,    -- 현재 수집 안됨
                        c.description,
                        c.major_index, -- Added
                        (
                            SELECT json_agg(json_build_object(
                                'date', to_char(news_date, 'YYYY-MM-DD'),
                                'title', title,
                                'link', link,
                                'source', source,
                                'sentiment', sentiment_label
                            ) ORDER BY news_date DESC)
                            FROM (
                                SELECT news_date, title, link, source, sentiment_label
                                FROM {SCHEMA_NAME}.us_stock_news news
                                WHERE news.stock_code = c.stock_code
                                {'AND news.news_date <= %s' if target_date else ''}
                                ORDER BY news_date DESC
                                LIMIT 5
                            ) sub_news
                        ) as news
                    FROM {SCHEMA_NAME}.us_stock_companies c
                    LEFT JOIN {SCHEMA_NAME}.us_stock_prices p ON c.stock_code = p.stock_code 
                        AND p.trade_date = {'%s' if target_date else f"(SELECT MAX(trade_date) FROM {SCHEMA_NAME}.us_stock_prices WHERE stock_code = c.stock_code)"}
                    LEFT JOIN {SCHEMA_NAME}.us_stock_analysis a ON c.stock_code = a.stock_code 
                        AND a.analysis_date = {'%s' if target_date else f"(SELECT MAX(analysis_date) FROM {SCHEMA_NAME}.us_stock_analysis WHERE stock_code = c.stock_code)"}
                    LEFT JOIN {SCHEMA_NAME}.us_stock_fundamentals f ON c.stock_code = f.stock_code
                        AND f.base_date = (SELECT MAX(base_date) FROM {SCHEMA_NAME}.us_stock_fundamentals WHERE stock_code = c.stock_code)
                    ORDER BY {order_clause}
                """
                if limit:
                    sql += f" LIMIT {limit}"
                
                query_params = []
                if target_date:
                    query_params.append(target_date) # price_history
                    query_params.append(target_date) # news (added)
                    query_params.append(target_date) # us_stock_prices
                    query_params.append(target_date) # us_stock_analysis
                
                cur.execute(sql, tuple(query_params))
                rows = cur.fetchall()
                
                return rows
        except Exception as e:
            print(f"미국 시장 조회 실패: {e}")
            self.conn.rollback()
            return []

    def get_us_stock_news(self, stock_code, limit=5):
        """
        특정 종목의 최신 뉴스 조회
        """
        if not self.conn:
            return []
        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    SELECT news_date, title, link, source, sentiment_label
                    FROM {SCHEMA_NAME}.us_stock_news
                    WHERE stock_code = %s
                    ORDER BY news_date DESC
                    LIMIT %s
                """
                cur.execute(sql, (stock_code, limit))
                return cur.fetchall()
        except Exception as e:
            print(f"뉴스 조회 실패 ({stock_code}): {e}")
            return []

    def insert_daily_price_optimized(self, stock_code, price_data):
        """
        파티셔닝된 daily_price 테이블에 시세 데이터 저장 (단건)
        price_data: {'date': '2025-01-01', 'open': ..., 'close': ...}
        """
        if not self.conn:
            return False
            
        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.daily_price
                    (stock_code, trade_date, open_price, high_price, low_price, close_price, volume, amount)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume,
                    amount = EXCLUDED.amount
                """
                
                # 날짜 처리
                trade_date = price_data.get('date') or price_data.get('stck_bsop_date')
                if isinstance(trade_date, str) and len(trade_date) == 8:
                    trade_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
                
                # 값 처리 (None 체크)
                def get_float(k):
                    v = price_data.get(k)
                    return float(v) if v else None
                def get_int(k):
                    v = price_data.get(k)
                    return int(v) if v else None

                cur.execute(sql, (
                    stock_code,
                    trade_date,
                    get_float('open') or get_float('stck_oprc') or get_float('open_price'),
                    get_float('high') or get_float('stck_hgpr') or get_float('high_price'),
                    get_float('low') or get_float('stck_lwpr') or get_float('low_price'),
                    get_float('close') or get_float('stck_clpr') or get_float('close_price'),
                    get_int('volume') or get_int('acml_vol'),
                    get_int('amount') or get_int('acml_tr_pbmn')
                ))
            self.conn.commit()
            return True
        except Exception as e:
            # print(f"Daily price insert failed ({stock_code}): {e}")
            self.conn.rollback()
            return False

    def insert_daily_prices_optimized_batch(self, stock_code, price_data_list):
        """
        파티셔닝된 daily_price 테이블에 시세 데이터 저장 (배치)
        """
        if not self.conn or not price_data_list:
            return False

        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    INSERT INTO {SCHEMA_NAME}.daily_price
                    (stock_code, trade_date, open_price, high_price, low_price, close_price, volume, amount)
                    VALUES %s
                    ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume,
                    amount = EXCLUDED.amount
                """
                
                final_data = []
                for p in price_data_list:
                    trade_date = p.get('date') or p.get('stck_bsop_date')
                    if isinstance(trade_date, str) and len(trade_date) == 8:
                        trade_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"

                    def get_v(k): return p.get(k)

                    final_data.append((
                        stock_code,
                        trade_date,
                        float(get_v('open') or get_v('stck_oprc') or get_v('open_price') or 0),
                        float(get_v('high') or get_v('stck_hgpr') or get_v('high_price') or 0),
                        float(get_v('low') or get_v('stck_lwpr') or get_v('low_price') or 0),
                        float(get_v('close') or get_v('stck_clpr') or get_v('close_price') or 0),
                        int(get_v('volume') or get_v('acml_vol') or 0),
                        int(get_v('amount') or get_v('acml_tr_pbmn') or 0)
                    ))
                
                if final_data:
                    execute_values(cur, sql, final_data)
                    self.conn.commit()
                    return True
                return False
        except Exception as e:
            print(f"Batch insert failed ({stock_code}): {e}")
            self.conn.rollback()
            return False

    def get_stock_master_info(self):
        """
        국내 주식 마스터 테이블에서 종목 정보 조회
        Returns: [(short_code, std_code, kor_name, market_type), ...]
        """
        if not self.conn:
            return []
        try:
            with self.conn.cursor() as cur:
                sql = f"""
                    SELECT short_code, std_code, kor_name, market_type
                    FROM {SCHEMA_NAME}.stock_master
                    ORDER BY short_code ASC
                """
                cur.execute(sql)
                return cur.fetchall()
        except Exception as e:
            print(f"Stock master fetch failed: {e}")
            return []
    def get_daily_price_ohlcv(self, stock_code, limit=120, is_us=False):
        """
        최근 N일간의 OHLCV 데이터 조회 (차트용)
        - is_us=False: daily_price (신규, 파티셔닝) 조회 -> 부족 시 stock_prices (기존) 조회하여 병합
        - is_us=True: us_stock_prices (기존) 조회
        """
        if not self.conn:
            return []
        try:
            with self.conn.cursor() as cur:
                if is_us:
                    # 미국 주식: us_stock_prices 테이블 조회
                    sql_us = f"""
                        SELECT trade_date, open_price, high_price, low_price, close_price, volume
                        FROM {SCHEMA_NAME}.us_stock_prices
                        WHERE stock_code = %s
                        ORDER BY trade_date DESC
                        LIMIT %s
                    """
                    cur.execute(sql_us, (stock_code, limit))
                    return cur.fetchall() # 이미 최신순 정렬됨
                else:
                    # 국내 주식: daily_price + stock_prices 병합 로직 유지
                    # 1. New Table Query
                    sql_new = f"""
                        SELECT trade_date, open_price, high_price, low_price, close_price, volume
                        FROM {SCHEMA_NAME}.daily_price
                        WHERE stock_code = %s
                        ORDER BY trade_date DESC
                        LIMIT %s
                    """
                    cur.execute(sql_new, (stock_code, limit))
                    new_rows = cur.fetchall()
                    
                    # 데이터가 충분하면 바로 반환
                    if len(new_rows) >= limit:
                        return new_rows
                    
                    # 2. Old Table Query (Fallback)
                    # 부족한 만큼 더 가져옴 (중복 날짜 제외 필요하나, 보통 날짜만 다르면 됨)
                    needed = limit - len(new_rows)
                    
                    # daily_price의 가장 오래된 날짜 가져오기 (이 날짜 이전 데이터를 가져와야 함)
                    filter_date_clause = ""
                    if new_rows:
                        last_date = new_rows[-1][0] # trade_date is 1st column
                        filter_date_clause = f"AND trade_date < '{last_date}'"
                    
                    sql_old = f"""
                        SELECT trade_date, open_price, high_price, low_price, close_price, volume
                        FROM {SCHEMA_NAME}.stock_prices
                        WHERE stock_code = %s {filter_date_clause}
                        ORDER BY trade_date DESC
                        LIMIT %s
                    """
                    cur.execute(sql_old, (stock_code, needed))
                    old_rows = cur.fetchall()
                    
                    # 병합 (new_rows + old_rows) -> 날짜 내림차순 유지
                    # new_rows가 더 최신 데이터임.
                    combined = new_rows + old_rows
                    return combined
                
        except Exception as e:
            print(f"OHLCV fetch failed ({stock_code}, is_us={is_us}): {e}")
            return []
    def get_stock_description(self, stock_code, is_us=False):
        """
        종목 코드로 기업 개요(description) 조회
        """
        if not self.conn:
            return None
        try:
            table_name = "us_stock_companies" if is_us else "stock_companies"
            with self.conn.cursor() as cur:
                sql = f"SELECT description FROM {SCHEMA_NAME}.{table_name} WHERE stock_code = %s"
                cur.execute(sql, (stock_code,))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Description fetch failed ({stock_code}): {e}")
            return None

    # ──────────────────────────────────────────────
    # DB 뷰 / 함수 관리 (데이터 처리 로직 DB 이전)
    # ──────────────────────────────────────────────

    def setup_views_and_functions(self):
        """
        PostgreSQL VIEW 및 AI 점수 계산 함수를 생성/갱신합니다.
        export_to_web.py 실행 전 또는 배포 초기에 한 번만 실행하면 됩니다.
        이후에는 DB 수준에서 데이터 처리가 되므로 Python 측 재계산 불필요.
        """
        if not self.conn:
            return False

        ddl_view = f"""
CREATE OR REPLACE VIEW {SCHEMA_NAME}.v_latest_price_with_change AS
WITH unified AS (
    SELECT stock_code, trade_date, close_price, volume
    FROM {SCHEMA_NAME}.daily_price
    UNION ALL
    SELECT stock_code, trade_date, close_price, volume
    FROM {SCHEMA_NAME}.stock_prices
),
deduped AS (
    SELECT DISTINCT ON (stock_code, trade_date) stock_code, trade_date, close_price, volume
    FROM unified
    ORDER BY stock_code, trade_date
),
with_lag AS (
    SELECT
        stock_code,
        trade_date,
        close_price,
        volume,
        LAG(close_price) OVER (PARTITION BY stock_code ORDER BY trade_date) AS prev_close,
        ROW_NUMBER() OVER (PARTITION BY stock_code ORDER BY trade_date DESC) AS rn
    FROM deduped
)
SELECT
    stock_code,
    trade_date,
    close_price,
    volume,
    prev_close,
    CASE
        WHEN prev_close IS NOT NULL AND prev_close > 0
        THEN ROUND(((close_price - prev_close) / prev_close * 100)::numeric, 2)
        ELSE 0
    END AS change_rate
FROM with_lag
WHERE rn = 1;
"""

        ddl_function = f"""
CREATE OR REPLACE FUNCTION {SCHEMA_NAME}.calculate_korea_ai_scores(p_target_date DATE DEFAULT NULL)
RETURNS INTEGER AS $$
DECLARE
    v_target_date DATE;
    v_count INTEGER := 0;
BEGIN
    -- 기준일: 파라미터 없으면 가장 최근 거래일 사용
    SELECT COALESCE(p_target_date, MAX(trade_date))
    INTO v_target_date
    FROM {SCHEMA_NAME}.v_latest_price_with_change;

    IF v_target_date IS NULL THEN
        RETURN 0;
    END IF;

    -- AI 점수 계산 및 UPSERT
    WITH score_calc AS (
        SELECT
            c.stock_code,
            v_target_date AS analysis_date,
            LEAST(GREATEST(
                -- 기본 점수 (price_prediction 기반)
                CASE
                    WHEN a.price_prediction = 'UP'   THEN 60
                    WHEN a.price_prediction = 'DOWN'  THEN 30
                    ELSE 45
                END
                -- confidence 가중치 (최대 +15)
                + COALESCE(a.confidence_level * 15, 0)
                -- 등락률 보정 (범위: -5 ~ +10)
                + GREATEST(LEAST(COALESCE(lp.change_rate, 0), 10), -5)
                -- PER 보정
                + CASE
                    WHEN f.per > 0 AND f.per < 5  THEN 5
                    WHEN f.per >= 5  AND f.per < 10 THEN 3
                    WHEN f.per >= 10 AND f.per < 20 THEN 1
                    ELSE 0
                  END
                -- PBR 보정
                + CASE
                    WHEN f.pbr > 0 AND f.pbr < 0.5 THEN 5
                    WHEN f.pbr >= 0.5 AND f.pbr < 1.0 THEN 3
                    WHEN f.pbr >= 1.0 AND f.pbr < 2.0 THEN 1
                    ELSE 0
                  END
            , 10), 99)::INTEGER AS ai_score,
            COALESCE(a.price_prediction, 'HOLD') AS price_prediction
        FROM {SCHEMA_NAME}.stock_companies c
        LEFT JOIN {SCHEMA_NAME}.v_latest_price_with_change lp ON c.stock_code = lp.stock_code
        LEFT JOIN {SCHEMA_NAME}.stock_analysis a
            ON c.stock_code = a.stock_code
            AND a.analysis_date = (
                SELECT MAX(analysis_date)
                FROM {SCHEMA_NAME}.stock_analysis
                WHERE stock_code = c.stock_code
            )
        LEFT JOIN {SCHEMA_NAME}.stock_fundamentals f
            ON c.stock_code = f.stock_code
            AND f.base_date = (
                SELECT MAX(base_date)
                FROM {SCHEMA_NAME}.stock_fundamentals
                WHERE stock_code = c.stock_code
            )
        WHERE lp.close_price IS NOT NULL
    )
    INSERT INTO {SCHEMA_NAME}.stock_analysis
        (stock_code, analysis_date, ai_score, price_prediction, updated_at)
    SELECT
        stock_code, analysis_date, ai_score, price_prediction, NOW()
    FROM score_calc
    ON CONFLICT (stock_code, analysis_date) DO UPDATE
        SET ai_score        = EXCLUDED.ai_score,
            price_prediction = EXCLUDED.price_prediction,
            updated_at       = NOW();

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;
"""

        try:
            with self.conn.cursor() as cur:
                print("  [DB] Creating/updating v_latest_price_with_change VIEW...")
                cur.execute(ddl_view)
                print("  [DB] Creating/updating calculate_korea_ai_scores() FUNCTION...")
                cur.execute(ddl_function)
            self.conn.commit()
            print("  [DB] Views and functions setup complete.")
            return True
        except Exception as e:
            print(f"  [DB][ERROR] setup_views_and_functions failed: {e}")
            self.conn.rollback()
            return False

    def calculate_korea_ai_scores_in_db(self, target_date=None):
        """
        PostgreSQL 함수를 호출하여 국내 주식 AI 점수를 DB 내에서 계산·저장합니다.
        Python 레이어의 calculate_and_save_korea_scores() 대체.

        Returns:
            int: 업데이트된 종목 수 (실패 시 -1)
        """
        if not self.conn:
            return -1
        try:
            with self.conn.cursor() as cur:
                if target_date:
                    cur.execute(
                        f"SELECT {SCHEMA_NAME}.calculate_korea_ai_scores(%s::date)",
                        (target_date,)
                    )
                else:
                    cur.execute(f"SELECT {SCHEMA_NAME}.calculate_korea_ai_scores()")
                result = cur.fetchone()
            self.conn.commit()
            count = result[0] if result else 0
            print(f"  [DB] calculate_korea_ai_scores() → {count} rows updated.")
            return count
        except Exception as e:
            print(f"  [DB][ERROR] calculate_korea_ai_scores_in_db failed: {e}")
            self.conn.rollback()
            return -1
