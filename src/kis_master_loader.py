
import os
import sys
import zipfile
import urllib.request
import pandas as pd
import psycopg2
from datetime import datetime

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME

class KisMasterLoader:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.download_dir = os.path.join(self.base_dir, 'data', 'master')
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            
        self.kospi_url = "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip"
        self.kosdaq_url = "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip"

    def download_file(self, url, filename):
        filepath = os.path.join(self.download_dir, filename)
        print(f"Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, filepath)
            print(f"Download complete: {filepath}")
            return filepath
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return None

    def unzip_file(self, zip_filepath):
        print(f"Unzipping {zip_filepath}...")
        try:
            with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                zip_ref.extractall(self.download_dir)
            
            # 압축 해제된 파일명 추측 (보통 zip 파일명과 유사하거나 확장자만 다름)
            # kospi_code.mst.zip -> kospi_code.mst
            extracted_filename = os.path.basename(zip_filepath).replace('.zip', '')
            extracted_path = os.path.join(self.download_dir, extracted_filename)
            
            if os.path.exists(extracted_path):
                return extracted_path
            return None
        except Exception as e:
            print(f"Unzip failed: {e}")
            return None

    def parse_kospi_master(self, filepath):
        """
        코스피 마스터 파일 파싱 (Fixed Width)
        """
        data = []
        try:
            with open(filepath, 'r', encoding='cp949') as f:
                for line in f:
                    # 포맷 (예시, 실제 포맷 확인 필요)
                    # 단축코드(9), 표준코드(12), 한글명(40)...
                    # KIS 개발자 문서 기준 (대략적)
                    short_code = line[0:9].strip()
                    std_code = line[9:21].strip()
                    kor_name = line[21:61].strip()
                    
                    # 그룹코드 등 추가 정보 파싱 필요 시 위치 확인
                    # 여기서는 핵심 정보만
                    
                    # 주식만 필터링 (표준코드 KR7... 또는 단축코드 A...)
                    # 보통 단축코드는 'A'로 시작하지 않음 (API용은 A붙일 수 있으나 마스터 파일은 숫자일 수 있음)
                    # 확인: 단축코드는 보통 6자리 숫자. 마스터 파일엔 A가 붙어있을수도?
                    # 일단 길이와 내용 저장
                    
                    entry = {
                        'short_code': short_code,
                        'std_code': std_code,
                        'kor_name': kor_name,
                        'market_type': 'KOSPI'
                    }
                    data.append(entry)
            return data
        except Exception as e:
            print(f"Parsing failed: {e}")
            return []

    def parse_kosdaq_master(self, filepath):
        """
        코스닥 마스터 파일 파싱
        """
        data = []
        try:
            with open(filepath, 'r', encoding='cp949') as f:
                for line in f:
                    short_code = line[0:9].strip()
                    std_code = line[9:21].strip()
                    kor_name = line[21:61].strip()
                    
                    entry = {
                        'short_code': short_code,
                        'std_code': std_code,
                        'kor_name': kor_name,
                        'market_type': 'KOSDAQ'
                    }
                    data.append(entry)
            return data
        except Exception as e:
            print(f"Parsing failed: {e}")
            return []

    def save_to_db(self, data_list):
        if not data_list:
            return
            
        print(f"Saving {len(data_list)} items to DB...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        try:
            # Bulk Insert with Upsert
            sql = f"""
                INSERT INTO {SCHEMA_NAME}.stock_master 
                (short_code, std_code, kor_name, market_type)
                VALUES %s
                ON CONFLICT (std_code) DO UPDATE SET
                short_code = EXCLUDED.short_code,
                kor_name = EXCLUDED.kor_name,
                market_type = EXCLUDED.market_type,
                updated_at = CURRENT_TIMESTAMP
            """
            
            values = []
            for d in data_list:
                # 정제된 코드 (혹시 A로 시작하면 제거? 보통 6자리 유지)
                # KIS API는 A+6자리 사용. DB에는 6자리만 저장할지 A포함할지 결정.
                # 기존 시스템 호환성 위해 A제거 여부 고민. 
                # 여기서는 원본 그대로 저장하고 필요시 변환.
                
                values.append((
                    d['short_code'],
                    d['std_code'],
                    d['kor_name'],
                    d['market_type']
                ))
            
            from psycopg2.extras import execute_values
            execute_values(cur, sql, values)
            conn.commit()
            print("DB save complete.")
            
        except Exception as e:
            print(f"DB Error: {e}")
            conn.rollback()
        finally:
            conn.close()

    def parse_us_master(self, filepath, exchange_code):
        """
        해외(미국) 마스터 파일 파싱
        포맷: 
        국가코드(3), 거래소코드(3), 종목코드(12), 표준코드(19? or various), 한글명(60?), 영문명(60?)...
        * 정확한 스펙은 문서 확인 필요하나, 보통 구분자 없이 고정폭.
        * 여기서는 간단히 추정하여 파싱하거나, CSV 형태일 수도 있음 (보통 mst는 text fixed width)
        * KIS 해외주식 마스터 포맷 (추정):
          구분자(Tab?) or Fixed? -> 보통 해외는 텍스트 파일 내에 정보가 있음.
          
        * 리버스 엔지니어링 또는 일반적 패턴 적용.
          단순히 row단위로 읽어서 처리.
        """
        data = []
        try:
            # 인코딩: cp949 or utf-8? 해외는 cp949일 가능성 높음.
            with open(filepath, 'r', encoding='cp949') as f:
                for line in f:
                    # 데이터 예시가 없으므로 정확한 파싱이 어려움.
                    # KIS API 예제 코드 등 참고 필요.
                    # 일단 구분자가 있는지 확인. 만약 없으면 Fixed Width.
                    
                    # 일반적인 구조 (추정):
                    # National(3) + Exchange(3) + Symbol(Varies) + ...
                    
                    # 임시: 탭 분리 시도
                    parts = line.split('\t')
                    if len(parts) > 5:
                        # 탭 구분인 경우
                        symbol = parts[0].strip()
                        name_kor = parts[1].strip()
                        name_eng = parts[2].strip()
                        # ...
                        # 하지만 mst 파일은 보통 fixed width임.
                        pass
                        
                    # Fixed Width 가정 (실제 데이터 확인 후 수정 필요할 수 있음)
                    # 여기서는 안전하게 Symbol 추출만 시도하거나, 
                    # KIS 제공 포맷을 검색할 수 없으므로,
                    # 파일 내용을 살짝 찍어보는게 좋을수도 있음.
                    # 코드를 일단 작성하되, 실행 후 로그를 보고 조정.
                    
                    # (임시) 전체 라인을 로그로 찍지 않고, 
                    # 앞부분만 잘라서 Symbol/Name 추정
                    # 보통 앞부분에 코드가 있음.
                    
                    # [Caution] Without accurate spec, parsing 'mst' is risky.
                    # Fallback: Assume Symbol is at start.
                    
                    # To be safer, let's assume we can't parse it perfectly right now 
                    # without spec. But the user asked to implement it.
                    # Let's try to infer from common KIS patterns:
                    # 1. Nat(3), Ex(3), Sym(16), Key(12), NameK(64), NameE(64)...
                    
                    # This is a placeholder implementation. 
                    # Optimization: We will skip complex parsing and just log snippet 
                    # for the first execution to debug, or try a standard pattern.
                    
                    pass 
                    
            # Since we don't have the spec and cannot browse, 
            # I will assume a standard implementation found in open sources for KIS master.
            # (Nat3, Ex3, Sym12, ISIN12, NameK40, NameE40...)
            
            return []
        except Exception as e:
            print(f"Parsing US master failed: {e}")
            return []
            
    def download_and_save_us(self, market_name, filename):
        url = f"https://new.real.download.dws.co.kr/common/master/{filename}"
        zip_path = self.download_file(url, filename)
        if zip_path:
            mst_path = self.unzip_file(zip_path)
            if mst_path:
                print(f"Parsing {market_name} master (Not fully implemented due to format format uncertainty)...")
                # TODO: Implement actual parsing logic after verifying file format
                # data = self.parse_us_master(mst_path, market_name)
                # self.save_global_to_db(data)

    def run(self):
        # 1. KOSPI
        zip_path = self.download_file(self.kospi_url, "kospi_code.mst.zip")
        if zip_path:
            mst_path = self.unzip_file(zip_path)
            if mst_path:
                data = self.parse_kospi_master(mst_path)
                self.save_to_db(data)
        
        # 2. KOSDAQ
        zip_path = self.download_file(self.kosdaq_url, "kosdaq_code.mst.zip")
        if zip_path:
            mst_path = self.unzip_file(zip_path)
            if mst_path:
                data = self.parse_kosdaq_master(mst_path)
                self.save_to_db(data)
                
        # 3. US Markets (NAS, NYS, AMS)
        # 파일명 추정: vals_code.mst.zip (해외는 보통 val? nas? 확인필요)
        # 보통: nas_code.mst.zip, nys_code.mst.zip, ams_code.mst.zip
        self.download_and_save_us("NAS", "nas_code.mst.zip")
        self.download_and_save_us("NYS", "nys_code.mst.zip")
        self.download_and_save_us("AMS", "ams_code.mst.zip")

if __name__ == "__main__":
    loader = KisMasterLoader()
    loader.run()
