
import psycopg2
import sys
import os
import concurrent.futures
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG, SCHEMA_NAME

def get_translator():
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source='auto', target='ko')
    except ImportError:
        try:
            from googletrans import Translator
            return Translator()
        except ImportError:
            return None

def translate_name(item):
    """
    item: (stock_code, company_name)
    Returns: (stock_code, translated_name)
    """
    code, name = item
    
    # 1. Manual Overrides (Known glitches or preferences)
    manual_map = {
        "Apple Inc.": "애플",
        "Tesla, Inc.": "테슬라",
        "Microsoft Corporation": "마이크로소프트",
        "NVIDIA Corporation": "엔비디아",
        "Amazon.com, Inc.": "아마존",
        "Alphabet Inc.": "구글(알파벳)",
        "Alphabet Inc. (Class A)": "구글(알파벳)",
        "Alphabet Inc. (Class C)": "구글(알파벳)",
        "Meta Platforms, Inc.": "메타",
        "Berkshire Hathaway Inc.": "버크셔 해서웨이",
        "Netflix, Inc.": "넷플릭스",
        "Coca-Cola Company (The)": "코카콜라",
        "PepsiCo, Inc.": "펩시코",
        "Costco Wholesale Corporation": "코스트코",
        "McDonald's Corporation": "맥도날드",
        "Walt Disney Company (The)": "디즈니",
        "Starbucks Corporation": "스타벅스",
        "Nike, Inc.": "나이키",
        "Visa Inc.": "비자",
        "Mastercard Incorporated": "마스터카드",
        "Johnson & Johnson": "존슨앤드존슨",
        "Procter & Gamble Company (The)": "P&G",
        "Walmart Inc.": "월마트",
        "JPMorgan Chase & Co.": "JP모건 체이스",
        "Bank of America Corporation": "뱅크오브아메리카",
        "Exxon Mobil Corporation": "엑손모빌",
        "Chevron Corporation": "쉐브론",
        "Pfizer Inc.": "화이자",
        "Moderna, Inc.": "모더나",
        "Advanced Micro Devices, Inc.": "AMD",
        "Intel Corporation": "인텔",
        "Qualcomm Incorporated": "퀄컴",
        "Taiwan Semiconductor Manufacturing Company Ltd.": "TSMC",
        "ASML Holding N.V.": "ASML",
        "Broadcom Inc.": "브로드컴",
        "Adobe Inc.": "어도비",
        "Salesforce, Inc.": "세일즈포스",
        "Oracle Corporation": "오라클",
        "Cisco Systems, Inc.": "시스코",
        "International Business Machines Corporation": "IBM",
        "Uber Technologies, Inc.": "우버",
        "Airbnb, Inc.": "에어비앤비",
        "Boeing Company (The)": "보잉",
        "General Motors Company": "GM",
        "Ford Motor Company": "포드",
        "AT&T Inc.": "AT&T",
        "Verizon Communications Inc.": "버라이즌",
        "Realty Income Corporation": "리얼티 인컴",
        "The Travelers Companies, Inc.": "트래블러스",
        "Public Service Enterprise Group Incorporated": "PSEG",
        "U.S. Bancorp": "US뱅크",
        "The Bank of New York Mellon Corporation": "BNY 멜론",
        "Capital One Financial Corporation": "캐피탈 원",
        "American Express Company": "아메리칸 익스프레스",
        "Goldman Sachs Group, Inc. (The)": "골드만삭스",
        "Morgan Stanley": "모건 스탠리",
        "Citigroup Inc.": "씨티그룹",
        "Wells Fargo & Company": "웰스파고",
        "BlackRock, Inc.": "블랙록",
        "Charles Schwab Corporation (The)": "찰스 슈왑",
        "PayPal Holdings, Inc.": "페이팔",
        "Block, Inc.": "블록(스퀘어)",
        "Intuit Inc.": "인튜이트",
        "ServiceNow, Inc.": "서비스나우",
        "Palo Alto Networks, Inc.": "팔로알토 네트웍스",
        "Fortinet, Inc.": "포티넷",
        "Snowflake Inc.": "스노우플레이크",
        "Palantir Technologies Inc.": "팔란티어",
        "Unity Software Inc.": "유니티",
        "Roblox Corporation": "로블록스",
        "Coinbase Global, Inc.": "코인베이스",
        "Shopify Inc.": "쇼피파이",
        "MercadoLibre, Inc.": "메르카도리브레",
        "Sea Limited": "Sea (쇼피)",
        "Coupang, Inc.": "쿠팡",
        "Alibaba Group Holding Limited": "알리바바",
        "PDD Holdings Inc.": "핀 DuoDuo",
        "JD.com, Inc.": "징동닷컴",
        "Baidu, Inc.": "바이두",
        "NIO Inc.": "니오",
        "Li Auto Inc.": "리오토",
        "XPeng Inc.": "샤오펑",
        "Toyota Motor Corporation": "도요타",
        "Honda Motor Co., Ltd.": "혼다",
        "Sony Group Corporation": "소니",
        "Nintendo Co., Ltd.": "닌텐도",
        "LVMH Moët Hennessy - Louis Vuitton, Société Européenne": "LVMH (루이비통)",
        "L'Oréal S.A.": "로레알",
        "Hermès International Société en commandite par actions": "에르메스",
        "Inditex, S.A.": "인디텍스 (자라)",
        "Volkswagen AG": "폭스바겐",
        "Siemens Aktiengesellschaft": "지멘스",
        "SAP SE": "SAP",
        "Airbus SE": "에어버스",
        "Anheuser-Busch InBev SA/NV": "AB인베브",
        "Unilever PLC": "유니레버",
        "Shell plc": "쉘",
        "BP p.l.c.": "BP",
        "TotalEnergies SE": "토탈에너지스",
        "Rio Tinto Group": "리오틴토",
        "BHP Group Limited": "BHP",
        "Vale S.A.": "발레",
        "Petróleo Brasileiro S.A. - Petrobras": "페트로브라스",
        "Infosys Limited": "인포시스",
        "HDFC Bank Limited": "HDFC 은행",
        "ICICI Bank Limited": "ICICI 은행",
        "WEC Energy Group, Inc.": "WEC 에너지",
        "Freeport-McMoRan Inc.": "프리포트 맥모란",
        "Royal Caribbean Cruises Ltd.": "로얄 캐리비안",
        "Carnival Corporation & plc": "카니발",
        "Norwegian Cruise Line Holdings Ltd.": "노르웨이지안 크루즈",
        "Delta Air Lines, Inc.": "델타항공",
        "United Airlines Holdings, Inc.": "유나이티드항공",
        "American Airlines Group Inc.": "아메리칸항공",
        "Southwest Airlines Co.": "사우스웨스트항공",
        "Lockheed Martin Corporation": "록히드마틴",
        "Raytheon Technologies Corporation": "레이theon",
        "Northrop Grumman Corporation": "노스롭 그루먼",
        "General Dynamics Corporation": "제너럴 다이내믹스",
        "L3Harris Technologies, Inc.": "L3 해리스",
        "Caterpillar Inc.": "캐터필러",
        "Deere & Company": "존 디어",
        "3M Company": "3M",
        "Honeywell International Inc.": "하니웰",
        "General Electric Company": "GE",
        "Union Pacific Corporation": "유니온 퍼시픽",
        "United Parcel Service, Inc.": "UPS",
        "FedEx Corporation": "페덱스",
        "Waste Management, Inc.": "웨이스트 매니지먼트",
        "Republic Services, Inc.": "리퍼블릭 서비스",
        "NextEra Energy, Inc.": "넥스트에라 에너지",
        "Duke Energy Corporation": "듀크 에너지",
        "Southern Company (The)": "서던 컴퍼니",
        "Dominion Energy, Inc.": "도미니언 에너지",
        "American Electric Power Company, Inc.": "아메리칸 일렉트릭 파워",
        "Eli Lilly and Company": "일라이 릴리",
        "Merck & Co., Inc.": "머크",
        "Bristol-Myers Squibb Company": "BMS",
        "Amgen Inc.": "암젠",
        "Gilead Sciences, Inc.": "길리어드",
        "Regeneron Pharmaceuticals, Inc.": "리제네론",
        "Vertex Pharmaceuticals Incorporated": "버텍스",
        "Intuitive Surgical, Inc.": "인튜이티브 서지컬",
        "Stryker Corporation": "스트라이커",
        "Boston Scientific Corporation": "보스턴 사이언티픽",
        "Becton, Dickinson and Company": "벡톤 디킨슨",
        "Edwards Lifesciences Corporation": "에드워즈 라이프사이언시스",
        "Thermo Fisher Scientific Inc.": "써모 피셔",
        "Danaher Corporation": "다나허",
        "Abbott Laboratories": "애보트",
        "Medtronic plc": "메드트로닉",
        "Monster Beverage Corporation": "몬스터 베버리지",
        "Keurig Dr Pepper Inc.": "큐리그 닥터페퍼",
        "Kraft Heinz Company (The)": "크래프트 하인즈",
        "General Mills, Inc.": "제너럴 밀스",
        "Kellogg Company": "켈로그",
        "Hershey Company (The)": "허쉬",
        "Tyson Foods, Inc.": "타이슨 푸드",
        "Kroger Co. (The)": "크로거",
        "Target Corporation": "타겟",
        "Lowe's Companies, Inc.": "로우스",
        "Home Depot, Inc. (The)": "홈디포",
        "TJX Companies, Inc.": "TJX",
        "Ross Stores, Inc.": "로스 스토어",
        "O'Reilly Automotive, Inc.": "오라이리 오토모티브",
        "AutoZone, Inc.": "오토존",
        "Chipotle Mexican Grill, Inc.": "치폴레",
        "Yum! Brands, Inc.": "얌! 브랜드",
        "Marriott International, Inc.": "메리어트",
        "Hilton Worldwide Holdings Inc.": "힐튼",
        "Las Vegas Sands Corp.": "라스베가스 샌즈",
        "MGM Resorts International": "MGM 리조트",
        "Booking Holdings Inc.": "부킹 홀딩스",
        "Expedia Group, Inc.": "익스피디아",
        "Simon Property Group, Inc.": "사이먼 프로퍼티",
        "Prologis, Inc.": "프로로지스",
        "American Tower Corporation": "아메리칸 타워",
        "Crown Castle Inc.": "크라운 캐슬",
        "Equinix, Inc.": "에퀴닉스",
        "Digital Realty Trust, Inc.": "디지털 리얼티",
        "Public Storage": "퍼블릭 스토리지",
        "Extra Space Storage Inc.": "엑스트라 스페이스",
        "Vici Properties Inc.": "VICI 프로퍼티",
        "Gaming and Leisure Properties, Inc.": "게이밍 앤 레저",
        "Welltower Inc.": "웰타워",
        "Ventas, Inc.": "벤타스",
        "Alexandria Real Estate Equities, Inc.": "알렉산드리아",
        "Blackstone Inc.": "블랙스톤",
        "KKR & Co. Inc.": "KKR",
        "Apollo Global Management, Inc.": "아폴로",
        "Carlyle Group Inc. (The)": "칼라일",
        "T. Rowe Price Group, Inc.": "T. 로우 프라이스",
        "State Street Corporation": "스테이트 스트리트",
        "Northern Trust Corporation": "노던 트러스트",
        "Aon plc": "에이온",
        "Marsh & McLennan Companies, Inc.": "마쉬 앤 맥레넌",
        "Arthur J. Gallagher & Co.": "아서 J. 갤러거",
        "Willis Towers Watson Public Limited Company": "윌리스 타워스 왓슨",
        "Chubb Limited": "처브",
        "Progressive Corporation (The)": "프로그레시브",
        "Allstate Corporation (The)": "올스테이트",
        "MetLife, Inc.": "메트라이프",
        "Prudential Financial, Inc.": "푸르덴셜",
        "Aflac Incorporated": "아플락",
        "Humana Inc.": "휴마나",
        "Cigna Group (The)": "시그나",
        "CVS Health Corporation": "CVS 헬스",
        "Elevance Health, Inc.": "엘레반스 헬스",
        "UnitedHealth Group Incorporated": "유나이티드헬스",
        "Centene Corporation": "센틴",
        "HCA Healthcare, Inc.": "HCA 헬스케어",
        "Laboratory Corporation of America Holdings": "랩코프",
        "Quest Diagnostics Incorporated": "퀘스트 진단",
        "Illumina, Inc.": "일루미나",
        "Agilent Technologies, Inc.": "애질런트",
        "Mettler-Toledo International Inc.": "메틀러 토레도",
        "Keysight Technologies, Inc.": "키사이트",
        "Amphenol Corporation": "암페놀",
        "TE Connectivity Ltd.": "TE 커넥티비티",
        "Corning Incorporated": "코닝",
        "Motorola Solutions, Inc.": "모토로라 솔루션",
        "Arista Networks, Inc.": "아리스타 네트웍스",
        "Juniper Networks, Inc.": "주니퍼 네트웍스",
        "F5, Inc.": "F5",
        "VeriSign, Inc.": "베리사인",
        "Akamai Technologies, Inc.": "아카마이",
        "Okta, Inc.": "옥타",
        "CrowdStrike Holdings, Inc.": "크라우드스트라이크",
        "Zscaler, Inc.": "지스케일러",
        "Atlassian Corporation": "아틀라시안",
        "Workday, Inc.": "워크데이",
        "Autodesk, Inc.": "오토데스크",
        "Ansys, Inc.": "앤시스",
        "Cadence Design Systems, Inc.": "케이던스",
        "Synopsys, Inc.": "시놉시스",
        "KLA Corporation": "KLA",
        "Lam Research Corporation": "램리서치",
        "Applied Materials, Inc.": "어플라이드 머티어리얼즈",
        "Analog Devices, Inc.": "아날로그 디바이스",
        "Microchip Technology Incorporated": "마이크로칩",
        "NXP Semiconductors N.V.": "NXP",
        "ON Semiconductor Corporation": "온세미",
        "Skyworks Solutions, Inc.": "스카이웍스",
        "Qorvo, Inc.": "코보",
        "Monolithic Power Systems, Inc.": "MPS",
        "Enphase Energy, Inc.": "엔페이즈",
        "SolarEdge Technologies, Inc.": "솔라엣지",
        "First Solar, Inc.": "퍼스트 솔라",
        "Albemarle Corporation": "앨버말",
        "Livent Corporation": "리벤트",
        "Sociedad Química y Minera de Chile S.A.": "SQM",
        "Barrick Gold Corporation": "배릭 골드",
        "Newmont Corporation": "뉴몬트",
        "Nucor Corporation": "뉴코",
        "Steel Dynamics, Inc.": "스틸 다이내믹스",
        "Vulcan Materials Company": "벌칸 머티리얼즈",
        "Martin Marietta Materials, Inc.": "마틴 마리에타",
        "Sherwin-Williams Company (The)": "셔윈-윌리엄스",
        "PPG Industries, Inc.": "PPG",
        "Linde plc": "린데",
        "Air Products and Chemicals, Inc.": "에어 프로덕츠",
        "Ecolab Inc.": "이콜랩",
        "Corteva, Inc.": "코르테바",
        "Archer-Daniels-Midland Company": "ADM",
        "Bunge Global SA": "번지",
        "Mosaic Company (The)": "모자이크",
        "CF Industries Holdings, Inc.": "CF 인더스트리",
        "Nutrien Ltd.": "뉴트리엔",
        "Trimble Inc.": "트림블",
        "Garmin Ltd.": "가민",
        "Zebra Technologies Corporation": "지브라",
        "Rockwell Automation, Inc.": "록웰 오토메이션",
        "Emerson Electric Co.": "에머슨",
        "Parker-Hannifin Corporation": "파커 하니핀",
        "Eaton Corporation plc": "이튼",
        "Cummins Inc.": "커민스",
        "PACCAR Inc": "파카",
        "Old Dominion Freight Line, Inc.": "올드 도미니언",
        "J.B. Hunt Transport Services, Inc.": "JB 헌트",
        "C.H. Robinson Worldwide, Inc.": "CH 로빈슨",
        "Expeditors International of Washington, Inc.": "익스피디터스",
        "Fastenal Company": "패스널",
        "W.W. Grainger, Inc.": "그레인저",
        "Cintas Corporation": "신타스",
        "Copart, Inc.": "코파트",
        "CoStar Group, Inc.": "코스타 그룹",
        "Verisk Analytics, Inc.": "베리스크",
        "Equifax Inc.": "에퀴팩스",
        "Moody's Corporation": "무디스",
        "S&P Global Inc.": "S&P 글로벌",
        "MSCI Inc.": "MSCI",
        "FactSet Research Systems Inc.": "팩트셋",
        "Morningstar, Inc.": "모닝스타",
        "Broadridge Financial Solutions, Inc.": "브로드리지",
        "Fiserv, Inc.": "파이서브",
        "Fidelity National Information Services, Inc.": "FIS",
        "Global Payments Inc.": "글로벌 페이먼트",
        "FleetCor Technologies, Inc.": "플리트코",
        "Jack Henry & Associates, Inc.": "잭 헨리",
        "Paychex, Inc.": "페이첵스",
        "Automatic Data Processing, Inc.": "ADP"
    }
    
    # Check manual map first (partial match allowed for key phrases)
    for key, val in manual_map.items():
        if key.lower() == name.lower():
            return (code, val)
        if name.startswith(key): # e.g. Berkshire Hathaway Inc. Class B
            return (code, val)

    translator = get_translator()
    if not translator:
        return (code, name)

    try:
        translated = name
        if hasattr(translator, 'translate'): 
            if "googletrans" in str(type(translator)):
                res = translator.translate(name, dest='ko')
                translated = res.text
            else:
                translated = translator.translate(name)
        
        # Post-processing: remove common suffixes if translator kept them
        suffixes = [" Inc.", " Corporation", " Corp.", " Ltd.", " Company", " Co.", " PLC", " N.V.", " S.A.", " Group", " Holdings", " Technologies"]
        
        # If translation didn't change much (still english), try stripping suffixes and translating again
        # or if it contains " Inc" in Korean (which shouldn't happen usually)
        
        if translated == name:
             # Try stripping typical suffixes
            clean_name = name
            for s in suffixes:
                clean_name = clean_name.replace(s, "").strip()
                clean_name = clean_name.replace(s.upper(), "").strip()
            
            # Additional clean
            clean_name = clean_name.split(',')[0]

            if clean_name != name:
                if "googletrans" in str(type(translator)):
                    res = translator.translate(clean_name, dest='ko')
                    translated = res.text
                else:
                    translated = translator.translate(clean_name)

        return (code, translated)
    except Exception as e:
        # print(f"Error translating {name}: {e}")
        return (code, name)

def update_us_names():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("Fetching ALL US stocks to check against manual map...")
    cur.execute(f"""
        SELECT stock_code, company_name
        FROM {SCHEMA_NAME}.us_stock_companies 
    """)
    rows = cur.fetchall()
    print(f"Total count: {len(rows)}")
    
    if not rows:
        print("Nothing to translate.")
        return

    updated_data = []
    
    # We will process ALL rows to ensure manual map is applied even if DB has something else
    
    print("Processing...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(translate_name, r): r for r in rows}
        
        completed = 0
        total = len(rows)
        
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            # We add to updated_data regardless, to force update with 'correct' name
            # But maybe only if it differs from *current* DB value?
            # To be safe, we just update everything. It's only 500 rows.
            updated_data.append(res)
            
            completed += 1
            if completed % 100 == 0:
                print(f"  - Processed {completed}/{total}...")
    
    print(f"Updating DB with {len(updated_data)} names...")
    
    # Batch update
    update_query = f"""
        UPDATE {SCHEMA_NAME}.us_stock_companies
        SET korean_name = %s
        WHERE stock_code = %s
    """
    
    # (code, name) -> need (name, code) order for query
    batch_params = [(name, code) for code, name in updated_data]
    
    from psycopg2.extras import execute_batch
    execute_batch(cur, update_query, batch_params)
    
    conn.commit()
    print("Update Complete.")
    conn.close()

if __name__ == "__main__":
    update_us_names()
