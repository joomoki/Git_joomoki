import requests
import time

def get_usd_krw_rate():
    """
    USD/KRW 환율 조회
    무료 API 사용 (https://open.er-api.com/v6/latest/USD)
    실패 시 기본값(1400.0) 반환
    """
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get('result') == 'success':
            rates = data.get('rates', {})
            krw_rate = rates.get('KRW')
            if krw_rate:
                return float(krw_rate)
                
    except Exception as e:
        print(f"[WARNING] 환율 조회 실패: {e}")
    
    # 실패 시 대략적인 기본값 반환 (최근 환율 기준)
    return 1450.0

if __name__ == "__main__":
    rate = get_usd_krw_rate()
    print(f"Current USD/KRW Rate: {rate} KRW")
