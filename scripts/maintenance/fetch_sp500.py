import pandas as pd
import requests

import sys

import io

# Force UTF-8 output for Windows console
sys.stdout.reconfigure(encoding='utf-8')

def fetch_sp500_list():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Wikipedia table id is 'constituents'
        # Explicitly use 'lxml' or 'bs4' if needed, but default usually works if deps are installed.
        tables = pd.read_html(io.StringIO(response.text), attrs={'id': 'constituents'})
        sp500_df = tables[0]
        
        stocks = []
        for index, row in sp500_df.iterrows():
            symbol = row.get('Symbol')
            name = row.get('Security')
            sector = row.get('GICS Sector')
            
            if not symbol:
                continue
            
            # Basic heuristics for market
            market = "NAS" if len(symbol) >= 4 else "NYS"
            
            # Specific corrections
            known_nas = ["AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "AVGO", "COST", "PEP", "SBUX", "AMD", "INTC", "QCOM", "MU", "TXN", "AMAT", "ASML", "NFLX", "ADBE"]
            known_nys = ["TSM", "CRM", "ORCL", "IBM", "V", "MA", "JPM", "BAC", "BRK.B", "WMT", "KO", "MCD", "NKE"]
            
            if symbol in known_nas: market = "NAS"
            if symbol in known_nys: market = "NYS"
            
            stocks.append({
                "code": symbol,
                "market": market,
                "name": name,
                "korean_name": name, # Default to English name
                "sector": sector
            })
            
        return stocks

    except Exception as e:
        # Use repr to avoid UnicodeEncodeError in case of special chars in error message
        # And ensure we don't print massive HTML blobs if they are in the error
        err_msg = str(e)
        if len(err_msg) > 500:
            err_msg = err_msg[:500] + "..."
        print(f"Error fetching S&P 500 list: {err_msg}")
        return []

if __name__ == "__main__":
    sp500 = fetch_sp500_list()
    print(f"Fetched {len(sp500)} stocks.")
    
    # Write to src/us_stock_list.py
    file_path = "d:/joomoki_PJ/src/us_stock_list.py"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("# S&P 500 Stock List (Auto-generated)\n")
        f.write("# fields: code(티커), market(거래소), name(영문명), korean_name(한글명), sector(섹터)\n\n")
        f.write("US_TARGET_STOCKS = [\n")
        for s in sp500:
            # Escape quotes in names if necessary
            name = s['name'].replace('"', '\\"')
            korean_name = s['korean_name'].replace('"', '\\"')
            f.write(f"    {{'code': '{s['code']}', 'market': '{s['market']}', 'name': \"{name}\", 'korean_name': \"{korean_name}\", 'sector': '{s['sector']}'}},\n")
        f.write("]\n")
    print(f"Successfully updated {file_path}")
