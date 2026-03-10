from src.kis_client import KisApiClient
import json

def test_api():
    kis = KisApiClient()
    # 애플(AAPL) 정보 조회
    print("Testing get_overseas_stock_info for AAPL...")
    info = kis.get_overseas_stock_info('AAPL', 'NAS')
    
    if info:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print("Failed to get info.")

if __name__ == "__main__":
    test_api()
