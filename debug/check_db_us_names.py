
from stock_db_manager import StockDBManager

def check_us_names():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    target_codes = ['AAPL', 'TSLA', 'NVDA', 'AMZN', 'GOOGL', 'MSFT', 'QQQ', 'MU']
    
    print(f"Checking korean_name for: {target_codes}")
    
    try:
        with db.conn.cursor() as cur:
            # 1. us_stock_companies 테이블 확인
            format_strings = ','.join(['%s'] * len(target_codes))
            sql = f"""
                SELECT stock_code, company_name, korean_name 
                FROM joomoki_news.us_stock_companies 
                WHERE stock_code IN ({format_strings})
            """
            cur.execute(sql, tuple(target_codes))
            rows = cur.fetchall()
            
            print("\n[us_stock_companies Table Data]")
            for r in rows:
                print(f"Code: {r[0]}, Name: {r[1]}, Korean: {r[2]}")

            # 2. 추천 이력 쿼리 테스트
            print("\n[Recommendation Query Test]")
            sql_rec = """
                SELECT 
                    h.stock_code,
                    h.is_us,
                    CASE 
                        WHEN h.is_us THEN COALESCE(uc.korean_name, uc.company_name)
                        ELSE c.company_name 
                    END as resolved_name
                FROM joomoki_news.stock_recommendation_history h
                LEFT JOIN joomoki_news.stock_companies c ON h.stock_code = c.stock_code AND h.is_us = FALSE
                LEFT JOIN joomoki_news.us_stock_companies uc ON h.stock_code = uc.stock_code AND h.is_us = TRUE
                WHERE h.stock_code IN ('AAPL', 'MU', 'TSLA')
                LIMIT 5
            """
            cur.execute(sql_rec)
            rec_rows = cur.fetchall()
            for r in rec_rows:
                print(f"Code: {r[0]}, IsUS: {r[1]}, ResolvedName: {r[2]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    check_us_names()
