import sys
import os
import json
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager

def verify_signals():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection failed")
        return

    # 1. Check if signals column exists (implicitly by trying to save/load)
    stock_code = "005930" # Samsung Electronics
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Mock analysis data with signals
    analysis_data = {
        'date': today,
        'summary': 'Test Summary',
        'score': 2,
        'confidence': 0.8,
        'signals': [
            {"type": "POSITIVE", "msg": "Test Signal 1!"},
            {"type": "WARNING", "msg": "Test Signal 2!"}
        ]
    }

    print(f"Saving analysis result for {stock_code}...")
    if db.save_analysis_result(stock_code, analysis_data):
        print("Save successful.")
    else:
        print("Save failed.")
        
    # 2. Retrieve via get_filtered_stocks
    print("Retrieving filtered stocks...")
    # Mock criteria to match this stock (assuming it has price data)
    # If no price data, it won't show up. 
    # Let's hope 005930 has price data in DB. If not, we might need to insert dummy price.
    
    # Check if price exists
    if not db.get_close_price(stock_code, today):
        print("No price data for today, inserting dummy price...")
        db.insert_daily_prices(stock_code, [{
            'stck_bsop_date': today.replace('-', ''),
            'stck_oprc': '70000',
            'stck_hgpr': '71000',
            'stck_lwpr': '69000',
            'stck_clpr': '70500',
            'acml_vol': '1000000'
        }])

    # Also need fundamentals for filtering? 
    # get_filtered_stocks joins with fundamentals. 
    # If fundamentals key is missing, fields might be null but left join should preserve row?
    # Yes, LEFT JOIN.
    
    rows = db.get_filtered_stocks({'trend': None}) # Get all? limit is removed but logic might still restrict
    
    found = False
    for row in rows:
        if row[0] == stock_code:
            found = True
            print(f"Stock found: {row[1]} ({row[0]})")
            print(f"Signals column index 11: {row[11]}")
            
            # Verify signals content
            if isinstance(row[11], str):
                signals = json.loads(row[11])
            elif isinstance(row[11], list):
                signals = row[11]
            else:
                signals = []
                
            print(f"Parsed signals: {signals}")
            break
            
    if not found:
        print("Stock 005930 not found in filtered list.")
        # Debug: list all
        # print("List of all stocks found:", [r[0] for r in rows[:10]])

    db.disconnect()

if __name__ == "__main__":
    verify_signals()
