import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.db_config import SCHEMA_NAME
from src.stock_db_manager import StockDBManager

def create_table():
    db = StockDBManager()
    if db.connect():
        try:
            with open('sql/create_recommendation_table.sql', 'r', encoding='utf-8') as f:
                sql = f.read()
                with db.conn.cursor() as cur:
                    # 스키마 설정
                    cur.execute(f"SET search_path TO {SCHEMA_NAME}")
                    cur.execute(sql)
                db.conn.commit()
                print(f"[{SCHEMA_NAME}] 스키마에 테이블 생성 완료")
        except Exception as e:
            print(f"테이블 생성 실패: {e}")
        finally:
            db.disconnect()
    else:
        print("DB 연결 실패")

if __name__ == "__main__":
    create_table()
