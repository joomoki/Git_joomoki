
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager

def test_screener():
    db_manager = StockDBManager()
    if not db_manager.connect():
        print("DB Connection Failed")
        return

    print("\n[Test: Screener]")
    
    # Test 1: High Market Cap
    print("\n1. High Market Cap (> 100 Trillion KRW)")
    criteria = {'min_market_cap': 100000} # 100조 (input is in 억? No, get_filtered_stocks implementation multiplies by 100 million)
    # wait, main.py says: 'min_market_cap': int(data.get('min_market_cap'))
    # stock_db_manager.py says: conditions.append("f.market_cap >= %s"); params.append(criteria['min_market_cap'] * 100000000)
    # So if I pass 100000 (10조?), it becomes 100000 * 10^8 = 10^13 = 10 Trillion.
    # Samsung Electronics is ~500 Trillion.
    
    # 10000 (1조)
    criteria = {'min_market_cap': 10000} 
    results = db_manager.get_filtered_stocks(criteria)
    print(f"Found {len(results)} stocks with market cap > 10000억")
    for r in results[:5]:
        print(f" - {r[1]} ({r[0]}): Cap {r[10]}")

    # Test 2: Low PER
    print("\n2. Low PER (< 10)")
    criteria = {'max_per': 10.0}
    results = db_manager.get_filtered_stocks(criteria)
    print(f"Found {len(results)} stocks with PER < 10")
    for r in results[:5]:
        print(f" - {r[1]} ({r[0]}): PER {r[8]}")

    # Test 3: Up Trend
    print("\n3. UP Trend Prediction")
    criteria = {'trend': 'UP'}
    results = db_manager.get_filtered_stocks(criteria)
    print(f"Found {len(results)} stocks with UP prediction")
    for r in results[:5]:
        print(f" - {r[1]} ({r[0]}): Prediction {r[7]}")
        
    db_manager.disconnect()

if __name__ == "__main__":
    test_screener()
