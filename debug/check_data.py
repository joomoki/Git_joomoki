import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager

def check_db_data():
    db = StockDBManager()
    if not db.connect():
        print("DB Check Failed")
        return

    print("Checking Stock Prices...")
    with db.conn.cursor() as cur:
        # 최근 trade_date 확인
        cur.execute("SELECT DISTINCT trade_date FROM stock_db.stock_prices ORDER BY trade_date DESC LIMIT 10")
        dates = cur.fetchall()
        print("Recent Korea Stock Dates:", dates)
        
        cur.execute("SELECT DISTINCT trade_date FROM stock_db.us_stock_prices ORDER BY trade_date DESC LIMIT 10")
        us_dates = cur.fetchall()
        print("Recent US Stock Dates:", us_dates)

        # recommendation_history 확인
        cur.execute("SELECT * FROM stock_db.stock_recommendation_history ORDER BY recommendation_date DESC LIMIT 5")
        history = cur.fetchall()
        print("Recent Recommendations:", history)

    db.disconnect()

if __name__ == "__main__":
    check_db_data()
