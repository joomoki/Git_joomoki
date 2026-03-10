# 한국투자증권(KIS) API 인증 정보
# 이 파일을 'secrets.py'로 이름 변경 후 실제 값을 입력해주세요.
# 주의: 이 파일은 git 등에 커밋하지 마세요.

KIS_AUTH = {
    # 실전투자: "https://openapi.koreainvestment.com:9443"
    # 모의투자: "https://openapivts.koreainvestment.com:29443"
    "URL_BASE": "https://openapi.koreainvestment.com:9443",
    
    # 발급받은 App Key
    "APP_KEY": "PSNDmX7xt0ps891G8r0D5x3oQjCnaSKSdY15",
    
    # 발급받은 App Secret
    "APP_SECRET": "jLY7Adsm1qHQ5+NZYfTVXysh1M7KN7uT2pDB4KGrDTQ2wUspK+zHzRSMDj+tRc//M8cjOWH8mtdPYjoIMd2ej6ObfUgq4UHc4rUDaQ8CN7BVfYZZkBFUVQV6ZateyFTZ72npW1Kxzi1DDDTHGueS+ef3iQePjnWKk6Xy34Pe/iehZsLt/f4=",
    
    # 계좌번호 (선택사항, 주문이 아닌 시세 조회 시에는 필수가 아닐 수 있으나 토큰 발급 시 필요할 수 있음)
    "CANO": "YOUR_ACCOUNT_NUMBER_PREFIX", # 계좌번호 체계(8-2)의 앞 8자리
    "ACNT_PRDT_CD": "01",                 # 계좌번호 뒤 2자리
}
