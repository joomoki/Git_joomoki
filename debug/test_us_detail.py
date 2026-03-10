from src.kis_client import KisApiClient
import json
import requests

def test_detail():
    kis = KisApiClient()
    token = kis.get_access_token()
    if not token:
        print("토큰 발급 실패")
        return

    # 테스트할 API: 해외주식 종목 상세정보 (HHDFS76410000)
    url = kis.base_url + "/uapi/overseas-price/v1/quotations/search-info"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": kis.app_key,
        "appsecret": kis.app_secret,
        "tr_id": "HHDFS76410000"
    }
    
    params = {
        "AUTH": "",
        "EXCD": "NAS",
        "SYMB": "AAPL"
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        print(f"Status Code: {res.status_code}")
        if res.status_code == 200:
            print(json.dumps(res.json(), indent=2, ensure_ascii=False))
        else:
            print(res.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_detail()
