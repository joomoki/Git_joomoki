
import yfinance as yf
import psycopg2
import sys
import os
import concurrent.futures
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME
from src.stock_db_manager import StockDBManager

def get_translator():
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source='auto', target='ko')
    except ImportError:
        try:
            from googletrans import Translator
            return Translator()
        except ImportError:
            return None

def fetch_and_update_description(stock_code):
    """
    Fetch description from yfinance, translate, and update DB.
    """
    try:
        # yfinance ticker
        ticker = yf.Ticker(stock_code)
        info = ticker.info
        
        summary = info.get('longBusinessSummary') or info.get('description')
        if not summary:
            # print(f"No summary for {stock_code}")
            return False

        # Translate
        translator = get_translator()
        translated_summary = summary
        
        if translator:
            try:
                # Split if too long (Google Translate limits)
                if len(summary) > 3000:
                    summary = summary[:3000]
                
                if hasattr(translator, 'translate'):
                    if "googletrans" in str(type(translator)):
                        res = translator.translate(summary, dest='ko')
                        translated_summary = res.text
                    else:
                        translated_summary = translator.translate(summary)
            except Exception as e:
                print(f"Translation failed for {stock_code}: {e}")
                # Fallback to English summary or empty? 
                # Keeping English summary is better than nothing.
        
        # Save to DB
        db = StockDBManager()
        if db.connect():
            db.update_company_description(stock_code, translated_summary, is_us=True)
            db.disconnect()
            return True
        return False

    except Exception as e:
        print(f"Error processing {stock_code}: {e}")
        return False

def update_all_us_descriptions():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get all US stocks that don't have a description yet
    print("Fetching US stocks without description...")
    cur.execute(f"SELECT stock_code FROM {SCHEMA_NAME}.us_stock_companies WHERE description IS NULL")
    rows = cur.fetchall()
    print(f"Found {len(rows)} stocks to update.")
    conn.close()
    
    if not rows:
        return

    # Process in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks
        future_to_code = {executor.submit(fetch_and_update_description, row[0]): row[0] for row in rows}
        
        completed = 0
        total = len(rows)
        
        for future in concurrent.futures.as_completed(future_to_code):
            code = future_to_code[future]
            try:
                success = future.result()
                if success:
                    # print(f"Updated {code}")
                    pass
            except Exception as exc:
                print(f"{code} generated an exception: {exc}")
            
            completed += 1
            if completed % 10 == 0:
                print(f"Progress: {completed}/{total}...")

    print("US Stock description update complete.")

if __name__ == "__main__":
    update_all_us_descriptions()
