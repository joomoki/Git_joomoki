import requests
from bs4 import BeautifulSoup

def test_crawl(code):
    url = f"https://finance.naver.com/item/main.nhn?code={code}"
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        res = requests.get(url, headers=headers)
        # Naver often uses EUC-KR
        # print("Encoding detected:", res.encoding)
        # res.encoding = 'euc-kr' 
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        summary = soup.select_one('.summary_info')
        if summary:
            print(f"[{code}] Found summary:")
            print(summary.get_text(strip=True)[:100] + "...")
        else:
            print(f"[{code}] No summary found.")
            
            # Check if it has any other signals of being a valid page
            name_elem = soup.select_one('.wrap_company h2')
            if name_elem:
                print(f"Page Title: {name_elem.get_text(strip=True)}")
            else:
                print("Page structure might be different.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing Samsung Electronics (005930)...")
    test_crawl('005930')
    print("\nTesting Nexen Preferred (005725)...")
    test_crawl('005725')
