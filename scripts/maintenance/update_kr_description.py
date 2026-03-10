
import requests
from bs4 import BeautifulSoup
import psycopg2
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME
from src.stock_db_manager import StockDBManager

def get_company_description(stock_code):
    """
    네이버 금융에서 기업 개요 크롤링
    """
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None
        
        # Naver Finance uses UTF-8 mostly now, let requests detect it from headers
        # response.encoding = 'euc-kr' 

        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 기업 개요 찾기 (h4_sub_sub 클래스 아래 summary_info)
        summary_section = soup.select_one('.summary_info')
        if not summary_section:
            # 다른 구조 시도 (e.g. ETF 등은 다를 수 있음)
            return None
            
        # summary_info 안의 텍스트 추출 (보통 p 태그나 텍스트 노드)
        text = summary_section.get_text(separator="\n", strip=True)
        
        # 너무 긴 경우 앞부분만? (일단 전체 저장)
        return text

    except Exception as e:
        print(f"Error fetching description for {stock_code}: {e}")
        return None

def update_all_kr_descriptions():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    # Get stocks missing descriptions
    print("Fetching KR companies missing descriptions from DB...")
    stocks = db.get_stocks_missing_description(is_us=False)
    
    if not stocks:
        print("All stocks already have descriptions.")
        db.disconnect()
        return

    print(f"Found {len(stocks)} stocks missing descriptions.")
    
    count = 0
    for stock in stocks:
        code = stock[0]
        name = stock[2]
        print(f"Processing: {name} ({code}) ...")
        
        desc = get_company_description(code)
        if desc:
            db.update_company_description(code, desc, is_us=False)
            count += 1
            # print(f"Updated {stock[1]} ({code})")
        
        if count % 10 == 0:
            print(f"Progress: {count} updated...")
            
        time.sleep(0.1) # Be polite to Naver

    print(f"Finished updating {count} KR stock descriptions.")
    db.disconnect()

if __name__ == "__main__":
    update_all_kr_descriptions()
