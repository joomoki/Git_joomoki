import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME

def debug_query():
    print("=== Debug Query (Feb 19) ===")
    
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        with db.conn.cursor() as cur:
            # 1. Total & P View Counts
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.stock_companies")
            print(f"Total Companies: {cur.fetchone()[0]}")

            sql_p = f"""
                SELECT COUNT(*)
                FROM (
                    SELECT stock_code, trade_date, close_price
                    FROM (
                        SELECT stock_code, trade_date, close_price,
                               ROW_NUMBER() OVER (PARTITION BY stock_code ORDER BY trade_date DESC) as rn
                        FROM (
                            SELECT stock_code, trade_date, close_price FROM {SCHEMA_NAME}.daily_price
                            UNION ALL
                            SELECT stock_code, trade_date, close_price FROM {SCHEMA_NAME}.stock_prices
                        ) u
                    ) ranked
                    WHERE rn = 1
                ) p
            """
            cur.execute(sql_p)
            print(f"Subquery 'p' Count: {cur.fetchone()[0]}")

            # 1-2. Sample Comparisons
            print("\n--- Sample Comparison ---")
            cur.execute(f"SELECT stock_code, length(stock_code) FROM {SCHEMA_NAME}.stock_companies ORDER BY stock_code LIMIT 5")
            c_rows = cur.fetchall()
            print(f"stock_companies samples (code, len): {c_rows}")
            
            sql_p_sample = f"""
                SELECT stock_code, length(stock_code)
                FROM (
                    SELECT stock_code, trade_date, close_price
                    FROM (
                        SELECT stock_code, trade_date, close_price,
                               ROW_NUMBER() OVER (PARTITION BY stock_code ORDER BY trade_date DESC) as rn
                        FROM (
                            SELECT stock_code, trade_date, close_price FROM {SCHEMA_NAME}.daily_price
                            UNION ALL
                            SELECT stock_code, trade_date, close_price FROM {SCHEMA_NAME}.stock_prices
                        ) u
                    ) ranked
                    WHERE rn = 1
                ) p
                ORDER BY stock_code
                LIMIT 5
            """
            cur.execute(sql_p_sample)
            p_rows = cur.fetchall()
            print(f"p view samples (code, len): {p_rows}")
            print("-------------------------\n")

            # 1-3. NULL check in p
            sql_p_null = f"""
                SELECT COUNT(*)
                FROM (
                    SELECT stock_code, trade_date, close_price
                    FROM (
                        SELECT stock_code, trade_date, close_price,
                               ROW_NUMBER() OVER (PARTITION BY stock_code ORDER BY trade_date DESC) as rn
                        FROM (
                            SELECT stock_code, trade_date, close_price FROM {SCHEMA_NAME}.daily_price
                            UNION ALL
                            SELECT stock_code, trade_date, close_price FROM {SCHEMA_NAME}.stock_prices
                        ) u
                    ) ranked
                    WHERE rn = 1
                ) p
                WHERE close_price IS NULL
            """
            cur.execute(sql_p_null)
            print(f"p view 'close_price IS NULL' Count: {cur.fetchone()[0]}")

            # 2. Join Query Count
            sql2 = f"""
                SELECT COUNT(*), array_agg(c.stock_code)
                FROM {SCHEMA_NAME}.stock_companies c
                LEFT JOIN (
                    SELECT stock_code, trade_date, close_price
                    FROM (
                        SELECT stock_code, trade_date, close_price,
                               ROW_NUMBER() OVER (PARTITION BY stock_code ORDER BY trade_date DESC) as rn
                        FROM (
                            SELECT stock_code, trade_date, close_price FROM {SCHEMA_NAME}.daily_price
                            UNION ALL
                            SELECT stock_code, trade_date, close_price FROM {SCHEMA_NAME}.stock_prices
                        ) u
                        WHERE 1=1
                    ) ranked
                    WHERE rn = 1
                ) p ON c.stock_code = p.stock_code
                WHERE p.close_price IS NOT NULL
            """
            cur.execute(sql2)
            row = cur.fetchone()
            print(f"Join Query Count (No date filter): {row[0]}")
            if row[0] > 0:
                print(f"Sample joined codes: {row[1][:5]}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()

if __name__ == "__main__":
    debug_query()
