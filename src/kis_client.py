import requests
import json
import time
import os
import sys
from datetime import datetime

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config.secrets import KIS_AUTH
    import config.secrets
    print(f"DEBUG: Loaded secrets from {config.secrets.__file__}")
except ImportError:
    print("경고: config/secrets.py 파일을 찾을 수 없습니다. config/secrets_template.py를 복사하여 생성해주세요.")
    # 테스트를 위한 임시 값 (실행 시 에러 발생 가능)
    KIS_AUTH = {"URL_BASE": "", "APP_KEY": "", "APP_SECRET": "", "CANO": "", "ACNT_PRDT_CD": ""}

from config.kis_config import DEFAULT_HEADERS, API_ENDPOINTS

class KisApiClient:
    def __init__(self):
        self.base_url = KIS_AUTH["URL_BASE"]
        self.app_key = KIS_AUTH["APP_KEY"]
        self.app_secret = KIS_AUTH["APP_SECRET"]
        self.access_token = None
        self.token_expired = 0
        self.token_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'token.json')
    
    def get_access_token(self):
        """접근 토큰 발급 및 갱신 (파일 캐싱 포함)"""
        # 1. 메모리에 유효한 토큰이 있으면 반환
        if self.access_token and time.time() < self.token_expired:
            return self.access_token

        # 2. 파일에서 토큰 로드 시도
        if os.path.exists(self.token_file_path):
            try:
                with open(self.token_file_path, 'r') as f:
                    token_data = json.load(f)
                    
                # 유효기간 확인 (안전을 위해 1분 여유)
                if time.time() < token_data.get('expired_at', 0) - 60:
                    self.access_token = token_data['access_token']
                    self.token_expired = token_data['expired_at']
                    print(f"저장된 토큰을 사용합니다. (만료: {datetime.fromtimestamp(self.token_expired).strftime('%H:%M:%S')})")
                    return self.access_token
            except Exception as e:
                print(f"토큰 파일 로드 실패: {e}")

        # 3. 새로운 토큰 발급 요청
        url = self.base_url + API_ENDPOINTS["GET_TOKEN"]["path"]
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            # print(f"DEBUG: Requesting token from {url}")
            res = requests.post(url, json=body)
            res.raise_for_status()
            data = res.json()
            
            self.access_token = data["access_token"]
            self.token_expired = time.time() + data["expires_in"]
            
            # 파일에 저장
            with open(self.token_file_path, 'w') as f:
                json.dump({
                    'access_token': self.access_token,
                    'expired_at': self.token_expired
                }, f)
            
            print(f"새로운 Access Token이 발급되었습니다. (만료: {data['token_type']} {data['expires_in']}초)")
            return self.access_token
            
        except Exception as e:
            print(f"토큰 발급 실패: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"응답 내용: {e.response.text}")
            raise
            
        except Exception as e:
            print(f"토큰 발급 실패: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"응답 내용: {e.response.text}")
            raise

    def get_common_headers(self, tr_id):
        """공통 헤더 생성"""
        token = self.get_access_token()
        
        headers = DEFAULT_HEADERS.copy()
        headers["authorization"] = f"Bearer {token}"
        headers["appkey"] = self.app_key
        headers["appsecret"] = self.app_secret
        headers["tr_id"] = tr_id
        
        return headers

    def get_historical_price(self, stock_code, start_date, end_date):
        """
        국내주식 기간별 시세 조회 (FHKST03010100)
        start_date, end_date: YYYYMMDD 형식 문자열
        """
        config = API_ENDPOINTS["DAILY_CHART_PRICE"]
        url = self.base_url + config["path"]
        headers = self.get_common_headers(config["tr_id"])
        
        # 쿼리 파라미터
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",      # J: 주식, W: ELW
            "FID_INPUT_ISCD": stock_code,       # 종목코드
            "FID_INPUT_DATE_1": start_date,     # 조회 시작일자 (YYYYMMDD)
            "FID_INPUT_DATE_2": end_date,       # 조회 종료일자 (YYYYMMDD)
            "FID_PERIOD_DIV_CODE": "D",         # D: 일봉
            "FID_ORG_ADJ_PRC": "0",             # 0: 수정주가
        }
        
        try:
            # 시세 조회는 보통 0.1초 제한 등이 있으므로 약간의 지연
            time.sleep(0.1) 
            
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            
            data = res.json()
            if data['rt_cd'] != '0':
                print(f"API 오류 ({stock_code}): {data['msg1']}")
                return []
                
            return data.get('output2', []) # output2가 일별 데이터 리스트
            
        except Exception as e:
            print(f"과거 데이터 조회 실패 ({stock_code}): {e}")
            return []

    def get_daily_price(self, stock_code):
        """
        주식현재가 일자별 (FHKST01010400) - 최근 30일 데이터
        """
        config = API_ENDPOINTS["DAILY_PRICE"]
        url = self.base_url + config["path"]
        headers = self.get_common_headers(config["tr_id"])
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_PERIOD_DIV_CODE": "D", # D: 일, W: 주, M: 월
            "FID_ORG_ADJ_PRC": "0"      # 0: 수정주가
        }
        
        try:
            time.sleep(0.1)
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            
            data = res.json()
            if data['rt_cd'] != '0':
                print(f"API 오류 ({stock_code}): {data['msg1']}")
                return []
            
            return data.get('output', [])
            
        except Exception as e:
            print(f"일별 시세 조회 실패 ({stock_code}): {e}")
            return []

    def get_current_price_detailed(self, stock_code):
        """
        주식현재가 시세 (FHKST01010100) - 기본적 분석 지표 포함
        """
        config = API_ENDPOINTS.get("CURRENT_PRICE_DETAILED", None)
        if config:
            url = self.base_url + config["path"]
            tr_id = config["tr_id"]
        else:
            # config에 정의되지 않았을 경우 fallback
            url = self.base_url + "/uapi/domestic-stock/v1/quotations/inquire-price"
            tr_id = "FHKST01010100"

        headers = self.get_common_headers(tr_id)
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code
        }
        
        try:
            time.sleep(0.05) 
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            
            data = res.json()
            if data['rt_cd'] != '0':
                return None
            
            return data.get('output', None)
            
        except Exception as e:
            print(f"상세 시세 조회 실패 ({stock_code}): {e}")
            return None

    def get_investor_trend(self, stock_code):
        """
        투자자별 매매동향 (FHKST01010900)
        """
        url = self.base_url + "/uapi/domestic-stock/v1/quotations/inquire-investor"
        headers = self.get_common_headers("FHKST01010900")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code
        }
        
        try:
            time.sleep(0.05)
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            
            data = res.json()
            if data['rt_cd'] != '0':
                return []
            
            return data.get('output', [])
            
        except Exception as e:
            print(f"투자자 동향 조회 실패 ({stock_code}): {e}")
            return []

    def get_overseas_price_daily(self, stock_code, days=100, market_code="NAS"):
        """
        해외주식(미국) 기간별 시세 (HHDFS76240000)
        stock_code: 종목코드 (예: AAPL)
        market_code: 거래소코드 (NAS:나스닥, NYS:뉴욕, AMS:아멕스)
        """
        config = API_ENDPOINTS.get("OVERSEAS_PRICE_DAILY")
        if config:
            url = self.base_url + config["path"]
            tr_id = config["tr_id"]
        else:
            url = self.base_url + "/uapi/overseas-price/v1/quotations/dailyprice"
            tr_id = "HHDFS76240000"

        headers = self.get_common_headers(tr_id)
        
        # 오늘 날짜 (YYYYMMDD)
        import datetime
        today = datetime.datetime.now().strftime("%Y%m%d")
        
        params = {
            "AUTH": "",
            "EXCD": market_code,
            "SYMB": stock_code,
            "GUBN": "0",        # 0: 일간, 1: 주간, 2: 월간
            "BYMD": today,      # 조회기준일자 (오늘)
            "MODP": "1"         # 0: 수정주가미반영, 1: 수정주가반영
        }
        
        try:
            time.sleep(0.1)
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            
            data = res.json()
            if data['rt_cd'] != '0':
                print(f"해외주식 API 오류 ({stock_code}): {data['msg1']}")
                return []
                
            return data.get('output2', [])
            
        except Exception as e:
            print(f"해외주식 일별 시세 조회 실패 ({stock_code}): {e}")
            return []

    def get_overseas_price_detail(self, stock_code, market_code="NAS"):
        """
        해외주식(미국) 현재가 상세 (HHDFS00000300)
        """
        config = API_ENDPOINTS.get("OVERSEAS_PRICE_DETAIL")
        if config:
            url = self.base_url + config["path"]
            tr_id = config["tr_id"]
        else:
            url = self.base_url + "/uapi/overseas-price/v1/quotations/price-detail"
            tr_id = "HHDFS00000300"

        headers = self.get_common_headers(tr_id)
        
        params = {
            "AUTH": "",
            "EXCD": market_code,
            "SYMB": stock_code
        }
        
        try:
            time.sleep(0.05)
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            
            data = res.json()
            if data['rt_cd'] != '0':
                return None
            
            return data.get('output', None)
            
        except Exception as e:
            print(f"해외주식 상세 시세 조회 실패 ({stock_code}): {e}")
            return None

    def get_overseas_stock_info(self, stock_code, market_code="NAS"):
        """
        해외주식 종목 상세정보 (HHDFS76410000) - PER, EPS, 상장주식수 등 확인 가능
        """
        # URL: /uapi/overseas-price/v1/quotations/search-info
        url = self.base_url + "/uapi/overseas-price/v1/quotations/search-info"
        headers = self.get_common_headers("HHDFS76410000")
        
        params = {
            "AUTH": "",
            "EXCD": market_code,
            "SYMB": stock_code
        }
        
        try:
            time.sleep(0.1)
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            
            data = res.json()
            if data['rt_cd'] != '0':
                return None
            
            # 검색 결과 리스트에서 해당 종목 찾기
            output2 = data.get('output2', [])
            if output2:
                for item in output2:
                    if item.get('symb') == stock_code:
                        return item
                
                # 정확히 일치하는게 없으면 None 반환 (오염 방지)
                # print(f"  [Warning] {stock_code} 검색 결과 불일치: {[x.get('symb') for x in output2]}")
                return None
            
            return None
            
        except Exception as e:
            print(f"해외주식 정보 조회 실패 ({stock_code}): {e}")
            return None
