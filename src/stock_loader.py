import sys
import os
import FinanceDataReader as fdr
import psycopg2

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME
from src.stock_db_manager import StockDBManager

def reset_and_reload_stocks():
    print("=== 국내 전종목 주가 정보 새로고침 시작 ===")
    
    db_manager = StockDBManager()
    if not db_manager.connect():
        print("DB 연결 실패")
        return

    try:
        # 1. 기존 데이터 삭제 (Truncate)
        # 외래 키 제약 조건이 있으면 CASCADE 필요
        # 주의: 관련된 모든 데이터(시세, 뉴스 연관 등)가 삭제될 수 있음
        print("\n[1] 기존 데이터 삭제 중...")
        with db_manager.conn.cursor() as cur:
            tables = [
                'stock_analysis', 
                'stock_keywords', 
                'news_stock_relations', 
                'stock_prices', 
                'stock_companies'
            ]
            for table in tables:
                cur.execute(f"TRUNCATE TABLE {SCHEMA_NAME}.{table} CASCADE;")
                print(f"  - {table} 테이블 초기화 완료")
        db_manager.conn.commit()

        # 2. KRX 전종목 리스트 가져오기
        print("\n[2] KRX 전종목 리스트 다운로드 중 (FinanceDataReader)...")
        # KRX: KOSPI, KOSDAQ, KONEX 모두 포함
        df_krx = fdr.StockListing('KRX')
        print(f"  - 총 {len(df_krx)}개 종목 확인")

        # 3. DB 저장
        print("\n[3] DB 저장 중...")
        saved_count = 0
        
        for index, row in df_krx.iterrows():
            # FinanceDataReader 컬럼: Code, Name, Market, Sector, Industry, ListingDate, SettleMonth, Representative, HomePage, Region
            
            # Market (KOSPI, KOSDAQ, KONEX) 필터링 (선택사항)
            market_type = row.get('Market')
            if market_type not in ['KOSPI', 'KOSDAQ', 'KONEX']:
                continue

            # 상장일 포맷 처리
            listed_date = row.get('ListingDate')
            if isinstance(listed_date, str):
                try:
                    # YYYY-MM-DD 포맷이 아닐 경우 처리 필요할 수 있음
                    pass 
                except:
                    listed_date = None
            
            # Marcap(시가총액)은 StockListing('KRX')에는 안나옴. 
            # StockListing('KRX-DESC') 등을 쓰면 나올수도 있으나 문서 확인 필요.
            # 일단 fdr.StockListing('KRX') 결과에는 Marcap이 포함되어 있음 (Stocks 갯수만큼)
            # 2024년 기준 fdr.StockListing('KRX')에는 'Marcap' 컬럼이 있음.
            
            market_cap = row.get('Marcap')
            if hasattr(market_cap, 'item'): # numpy int64 변환
                market_cap = market_cap.item()
            if not market_cap or str(market_cap) == 'nan':
                market_cap = 0

            company_info = {
                'stock_code': row['Code'],
                'company_name': row['Name'],
                'market_type': market_type,
                'sector': row.get('Sector'),
                'market_cap': market_cap,
                'listed_date': listed_date
            }
            
            if db_manager.insert_stock_company(company_info):
                saved_count += 1
                if saved_count % 500 == 0:
                    print(f"  - {saved_count}개 저장 완료...")

        print(f"\n[완료] 총 {saved_count}개 종목 저장 완료")

    except Exception as e:
        print(f"\n에러 발생: {e}")
        import traceback
        traceback.print_exc()
        db_manager.conn.rollback()
    
    finally:
        db_manager.disconnect()
        print("=== 작업 종료 ===")

if __name__ == "__main__":
    reset_and_reload_stocks()
