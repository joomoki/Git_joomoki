import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager

def debug_manager():
    print("=== Debug Manager ===")
    
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        # get_market_stocks 호출 테스트
        print("Calling get_market_stocks(target_date='2026-02-19')...")
        stocks = db.get_market_stocks(limit=10, target_date='2026-02-19')
        print(f"Result count: {len(stocks)}")
        
        if stocks:
            print("First item:", stocks[0])
        else:
            print("No stocks returned.")
            
    except Exception as e:
        print(f"Error calling method: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    debug_manager()
