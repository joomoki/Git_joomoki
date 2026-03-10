
from stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME

def update_korean_names():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    # 주요 종목 한글 매핑
    name_mapping = {
        'AAPL': '애플',
        'TSLA': '테슬라',
        'NVDA': '엔비디아',
        'MSFT': '마이크로소프트',
        'AMZN': '아마존',
        'GOOGL': '구글 (알파벳 A)',
        'QQQ': '인베스코 QQQ',
        'MU': '마이크론 테크놀로지',
        'GLW': '코닝',
        'BAC': '뱅크 오브 아메리카',
        'VZ': '버라이즌',
        'PLTR': '팔란티어',
        'TSM': 'TSMC',
        'INTC': '인텔',
        'RCL': '로얄 캐리비안',
        'SNDK': '샌디스크', 
        'SPY': 'SPDR S&P 500',
        'IVV': 'iShares S&P 500',
        'VOO': 'Vanguard S&P 500',
        'QCOM': '퀄컴',
        'AMD': 'AMD',
        'NFLX': '넷플릭스',
        'META': '메타 플랫폼스'
    }
    
    print(f"Updating korean_name for {len(name_mapping)} stocks...")
    
    try:
        with db.conn.cursor() as cur:
            success_count = 0
            for code, kor_name in name_mapping.items():
                sql = f"""
                    UPDATE {SCHEMA_NAME}.us_stock_companies
                    SET korean_name = %s
                    WHERE stock_code = %s
                """
                cur.execute(sql, (kor_name, code))
                if cur.rowcount > 0:
                    success_count += 1
                    # print(f"Updated {code} -> {kor_name}")
            
            db.conn.commit()
            print(f"[SUCCESS] Updated {success_count} stocks.")
                
    except Exception as e:
        print(f"Error: {e}")
        db.conn.rollback()
    finally:
        db.disconnect()

if __name__ == "__main__":
    update_korean_names()
