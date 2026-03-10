
from stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME

def check_history_names():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        with db.conn.cursor() as cur:
            # 추천 이력에 있는 모든 US 종목 코드 조회
            sql = f"""
                SELECT DISTINCT h.stock_code
                FROM {SCHEMA_NAME}.stock_recommendation_history h
                WHERE h.is_us = TRUE
            """
            cur.execute(sql)
            codes = [r[0] for r in cur.fetchall()]
            
            if not codes:
                print("No US stocks in history.")
                return

            print(f"Found {len(codes)} US stocks in history: {codes}")
            
            # 해당 종목들의 korean_name 조회
            format_strings = ','.join(['%s'] * len(codes))
            sql_names = f"""
                SELECT stock_code, company_name, korean_name
                FROM {SCHEMA_NAME}.us_stock_companies
                WHERE stock_code IN ({format_strings})
            """
            cur.execute(sql_names, tuple(codes))
            rows = cur.fetchall()
            
            print("\n[Status Report]")
            missing_korean = []
            for r in rows:
                code, eng, kor = r
                print(f"[{code}] Eng: {eng} | Kor: {kor}")
                # 한글 이름이 없거나, 영문 이름과 같거나, 알파벳이 포함된 경우 (단순 체크)
                if not kor or kor == eng or any(c.isalpha() for c in kor if c != ' '): # 간단한 알파벳 체크
                     # 'SK텔레콤' 같은 경우 알파벳 포함되므로 주의. 여기선 US 종목만 대상.
                     # 영어만 있는 경우를 찾기 위해
                     pass
                
                # 명시적으로 비어있거나 영문과 완전 동일한 경우 체크
                if not kor or kor.strip() == eng.strip():
                    missing_korean.append(code)

            if missing_korean:
                print(f"\n[MISSING KOREAN DRIVERS] {missing_korean}")
            else:
                print("\nAll historical US stocks have distinct Korean names (or at least mapped).")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    check_history_names()
