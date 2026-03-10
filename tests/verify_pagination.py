
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager

def test_pagination_sorting():
    db_manager = StockDBManager()
    if not db_manager.connect():
        print("DB Connection Failed")
        return

    print("\n[Test: Pagination & Sorting]")
    
    # 1. Count
    count = db_manager.get_market_stock_count()
    print(f"Total Stocks: {count}")
    
    if count == 0:
        print("No stocks found. Skipping tests.")
        return

    # 2. Sort by Market Cap (Default) - Page 1
    print("\n--- Sort by Market Cap (Page 1, Limit 5) ---")
    stocks = db_manager.get_market_stocks(page=1, limit=5, sort_by='market_cap')
    for s in stocks:
        print(f"{s[1]} ({s[0]}): Cap {s[11]}")
    
    # Verify order (Desc)
    caps = [s[11] for s in stocks if s[11] is not None]
    is_sorted = all(caps[i] >= caps[i+1] for i in range(len(caps)-1))
    print(f"Sorted by Cap (DESC): {is_sorted}")

    # 3. Sort by PER (ASC) - Page 1
    print("\n--- Sort by PER (Page 1, Limit 5) ---")
    stocks = db_manager.get_market_stocks(page=1, limit=5, sort_by='per')
    for s in stocks:
        print(f"{s[1]} ({s[0]}): PER {s[9]}")

    # Verify order (ASC) - ignoring None if any (though query uses NULLS LAST)
    pers = [s[9] for s in stocks if s[9] is not None]
    is_sorted_per = all(pers[i] <= pers[i+1] for i in range(len(pers)-1))
    print(f"Sorted by PER (ASC): {is_sorted_per}")

    # 4. Sort by Prediction (UP first)
    print("\n--- Sort by Prediction (Page 1, Limit 5) ---")
    stocks = db_manager.get_market_stocks(page=1, limit=5, sort_by='prediction')
    for s in stocks:
        print(f"{s[1]} ({s[0]}): Prediction {s[8]}, Cap {s[11]}")

    # 5. Pagination - Page 2
    print("\n--- Pagination (Page 2, Limit 5) ---")
    stocks_p1 = db_manager.get_market_stocks(page=1, limit=5, sort_by='market_cap')
    stocks_p2 = db_manager.get_market_stocks(page=2, limit=5, sort_by='market_cap')
    
    print("Page 1 first:", stocks_p1[0][1])
    print("Page 2 first:", stocks_p2[0][1])
    
    if stocks_p1[0][0] != stocks_p2[0][0]:
        print("Pagination seems correct (different items).")
    else:
        print("Pagination Failed (Same items).")

    db_manager.disconnect()

if __name__ == "__main__":
    test_pagination_sorting()
