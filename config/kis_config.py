# KIS API 설정 파일

# 기본 헤더 설정 (Content-Type 등)
DEFAULT_HEADERS = {
    "content-type": "application/json; charset=utf-8",
    "authorization": "",
    "appkey": "",
    "appsecret": "",
    "tr_id": "",
    "custtype": "P", # P: 개인, B: 법인
}

# API 엔드포인트 및 TR ID
API_ENDPOINTS = {
    # 접근 토큰 발급
    "GET_TOKEN": {
        "path": "/oauth2/tokenP",
        "method": "POST"
    },
    
    # 국내주식기간별시세 (일/주/월/년)
    # Docs: https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice
    "DAILY_CHART_PRICE": {
        "path": "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
        "tr_id": "FHKST03010100",
        "method": "GET"
    },
    
    # 주식현재가 일자별 (최근 30일)
    # Docs: https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-daily-price
    "DAILY_PRICE": {
        "path": "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
        "tr_id": "FHKST01010400",
        "method": "GET"
    }
}
