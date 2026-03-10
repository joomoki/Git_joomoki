import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.db_config import SCHEMA_NAME
from src.stock_db_manager import StockDBManager

def clear_history():
    db = StockDBManager()
    if db.connect():
        try:
            with db.conn.cursor() as cur:
                # 스키마 설정
                cur.execute(f"SET search_path TO {SCHEMA_NAME}")
                
                # 2026-02-09 이후 데이터만 삭제 (추가 요청)
                target_date_str = '2026-02-09'
                cur.execute(f"DELETE FROM {SCHEMA_NAME}.stock_recommendation_history WHERE recommendation_date >= %s", (target_date_str,))
                
            db.conn.commit()
            print(f"[{SCHEMA_NAME}.stock_recommendation_history] 테이블에서 {target_date_str} 이후 데이터 삭제 완료")
        except Exception as e:
            print(f"데이터 삭제 실패: {e}")
            db.conn.rollback()
        finally:
            db.disconnect()
    else:
        print("DB 연결 실패")

if __name__ == "__main__":
    clear_history()
