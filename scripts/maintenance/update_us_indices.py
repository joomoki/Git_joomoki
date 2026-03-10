
import requests
import psycopg2
import sys
import os
import io
import pandas as pd

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def fetch_sp500_tickers():
    """Wikipedia에서 S&P 500 종목 코드 수집"""
    print("Fetching S&P 500 list...")
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch S&P 500: {response.status_code}")
            return []
            
        tables = pd.read_html(io.StringIO(response.text), attrs={'id': 'constituents'})
        df = tables[0]
        tickers = df['Symbol'].tolist()
        # Clean tickers (e.g., BRK.B -> BRK-B is handled differently in some APIs, but let's keep as is or match DB)
        # Our DB usually has original ticker. Yahoo uses '-'
        return tickers
    except Exception as e:
        print(f"Error fetching S&P 500: {e}")
        return []

def fetch_dow30_tickers():
    """Wikipedia에서 Dow 30 종목 코드 수집"""
    print("Fetching Dow 30 list...")
    try:
        url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch Dow 30: {response.status_code}")
            return []
            
        tables = pd.read_html(io.StringIO(response.text), attrs={'id': 'constituents'})
        df = tables[0]
        tickers = df['Symbol'].tolist()
        return tickers
    except Exception as e:
        print(f"Error fetching Dow 30: {e}")
        return []

def fetch_nasdaq100_tickers():
    """Wikipedia에서 Nasdaq 100 종목 코드 수집"""
    print("Fetching Nasdaq 100 list...")
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch Nasdaq 100: {response.status_code}")
            return []
            
        tables = pd.read_html(io.StringIO(response.text), attrs={'id': 'constituents'})
        df = tables[0]
        tickers = df['Symbol'].tolist()
        return tickers
    except Exception as e:
        print(f"Error fetching Nasdaq 100: {e}")
        return []

def update_db_indices():
    """DB에 지수 정보 업데이트"""
    sp500 = set(fetch_sp500_tickers())
    dow30 = set(fetch_dow30_tickers())
    nasdaq100 = set(fetch_nasdaq100_tickers())
    
    print(f"Collected: S&P500({len(sp500)}), Dow30({len(dow30)}), Nasdaq100({len(nasdaq100)})")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Reset existing major_index
        cur.execute(f"UPDATE {SCHEMA_NAME}.us_stock_companies SET major_index = NULL")
        
        # 2. Get all stocks from DB
        cur.execute(f"SELECT stock_code FROM {SCHEMA_NAME}.us_stock_companies")
        db_stocks = cur.fetchall()
        
        updates = []
        
        for row in db_stocks:
            code = row[0]
            # DB Ticker Formatting fix (e.g. if DB has BRK.B and list as BRK-B)
            # Normalize to match list
            
            indices = []
            
            # Check membership
            # Handle . vs - difference if any
            check_code = code
            
            if code in dow30:
                indices.append("Dow30")
                
            if code in sp500:
                indices.append("S&P500")
                
            if code in nasdaq100:
                indices.append("Nasdaq100")
            
            if not indices and '.' in code:
                # Try replacing . with -
                alt_code = code.replace('.', '-')
                if alt_code in dow30: indices.append("Dow30")
                if alt_code in sp500: indices.append("S&P500")
                if alt_code in nasdaq100: indices.append("Nasdaq100")
            
            if indices:
                # Priority: Dow > SP > Nas (or combine?)
                # User asked for "S&P500인지 나스닥인지 다우산업인지"
                # Let's join them via slash if multiple? e.g. "S&P500/Nasdaq100"
                # But space is limited. Let's pick the most representative or join.
                # Common overlap: SP500 & Nasdaq100 -> S&P500/Nasdaq
                # Dow is most exclusive.
                
                # Sort order: Dow30, S&P500, Nasdaq100
                display_indices = []
                if "Dow30" in indices: display_indices.append("Dow30")
                if "S&P500" in indices: display_indices.append("S&P500")
                if "Nasdaq100" in indices: display_indices.append("Nas100") 
                
                final_str = "/".join(display_indices)
                updates.append((final_str, code))

        print(f"Updating {len(updates)} stocks with index info...")
        
        # Batch update
        sql = f"UPDATE {SCHEMA_NAME}.us_stock_companies SET major_index = %s WHERE stock_code = %s"
        from psycopg2.extras import execute_batch
        execute_batch(cur, sql, updates)
        
        conn.commit()
        print("Update completed successfully.")
        
    except Exception as e:
        print(f"Error updating DB: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    update_db_indices()
