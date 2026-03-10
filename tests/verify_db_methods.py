
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager

def test_search_stocks():
    db_manager = StockDBManager()
    if not db_manager.connect():
        print("DB Connection Failed")
        return

    print("\n[Test: search_stocks]")
    query = "삼성" # 삼성전자가 검색되길 기대
    results = db_manager.search_stocks(query)
    print(f"Query: '{query}' -> Found: {len(results)} items")
    for r in results:
        print(f" - {r}")
    
    # 코드로 검색
    query = "005930"
    results = db_manager.search_stocks(query)
    print(f"Query: '{query}' -> Found: {len(results)} items")
    for r in results:
        print(f" - {r}")

    db_manager.disconnect()

def test_get_daily_prices():
    db_manager = StockDBManager()
    if not db_manager.connect():
        print("DB Connection Failed")
        return

    print("\n[Test: get_daily_prices]")
    stock_code = "005930" # Samsung Electronics
    limit = 10
    prices = db_manager.get_daily_prices(stock_code, limit)
    print(f"Stock: {stock_code}, Limit: {limit} -> Found: {len(prices)} items")
    
    if prices:
        print("First item:", prices[0])
        print("Last item:", prices[-1])
        
        # 날짜 정렬 확인
        dates = [p[0] for p in prices]
        is_sorted = all(dates[i] <= dates[i+1] for i in range(len(dates)-1))
        print(f"Date Sorted (ASC): {is_sorted}")
    else:
        print("No price data found.")

    db_manager.disconnect()

if __name__ == "__main__":
    test_search_stocks()
    test_get_daily_prices()
