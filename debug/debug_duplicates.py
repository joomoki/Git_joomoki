
import sys
import os
import json
sys.path.append(os.getcwd())
from src.stock_db_manager import StockDBManager
from src.exchange_rate import get_usd_krw_rate
from config.db_config import SCHEMA_NAME # might need this if config loads it

def main():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        cur = db.conn.cursor()
        

        # 1. Check stock_companies for 판도라티비
        print("\n--- checking stock_companies for 판도라티비 ---")
        cur.execute(f"SELECT stock_code, company_name, market_type FROM {SCHEMA_NAME}.stock_companies WHERE company_name LIKE '%판도라티비%'")
        rows = cur.fetchall()
        for r in rows:
            print(r)

        # 2. Check for any stock_code with multiple entries in stock_companies
        print("\n--- checking stock_companies duplicates ---")
        cur.execute(f"SELECT stock_code, count(*) FROM {SCHEMA_NAME}.stock_companies GROUP BY stock_code HAVING count(*) > 1")
        dups = cur.fetchall()
        print(f"Duplicate stock_codes in stock_companies: {dups}")

        # 3. Simulate get_market_stocks for 판도라티비
        print("\n--- Simulate get_market_stocks for 판도라티비 ---")
        # We need to find the stock code first.
        if rows:
            target_code = rows[0][0]
            print(f"Target Code: {target_code}")
            
            # Use the query from stock_db_manager.get_market_stocks but filtered by stock_code
            # Also fix table names with schema
            sql = f"""
                SELECT 
                    c.stock_code, 
                    c.company_name, 
                    a.ai_score
                FROM {SCHEMA_NAME}.stock_companies c
                LEFT JOIN {SCHEMA_NAME}.daily_price p ON c.stock_code = p.stock_code 
                    AND p.trade_date = (SELECT MAX(trade_date) FROM {SCHEMA_NAME}.daily_price WHERE stock_code = c.stock_code)
                LEFT JOIN {SCHEMA_NAME}.stock_analysis a ON c.stock_code = a.stock_code 
                    AND a.analysis_date = (SELECT MAX(analysis_date) FROM {SCHEMA_NAME}.stock_analysis WHERE stock_code = c.stock_code)
                WHERE c.company_name LIKE '%판도라티비%'
            """
            cur.execute(sql)
            results = cur.fetchall()
            print(f"Query Result Count: {len(results)}")
            for res in results:
                print(res)

        # 4. Check sorting logic verification
        # Retrieve a few stocks and their scores to see if there's any anomaly in how they are stored vs viewed
        print("\n--- Check Top 5 Stocks by Score in DB ---")
        cur.execute(f"""
            SELECT c.company_name, a.ai_score 
            FROM {SCHEMA_NAME}.stock_analysis a 
            JOIN {SCHEMA_NAME}.stock_companies c ON a.stock_code = c.stock_code
            WHERE a.analysis_date = (SELECT MAX(analysis_date) FROM {SCHEMA_NAME}.stock_analysis WHERE stock_code = a.stock_code)
            ORDER BY a.ai_score DESC 
            LIMIT 5
        """)
        top5 = cur.fetchall()
        print("Top 5 by Score in DB:", top5)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()
