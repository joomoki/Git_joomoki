import sys
import os
import json
# 프로젝트 루트 경로 추가 (scripts의 상위 폴더)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.kis_client import KisApiClient
from config.kis_config import API_ENDPOINTS

def test_current_price_detailed():
    client = KisApiClient()
    # 삼성전자
    code = "005930"
    
    # FHKST01010100 (주식현재가 시세) 테스트
    # kis_client에 메서드가 없으므로 직접 호출 테스트
    url = client.base_url + "/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = client.get_common_headers("FHKST01010100")
    
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code
    }
    
    try:
        import requests
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(e)

if __name__ == "__main__":
    test_current_price_detailed()
