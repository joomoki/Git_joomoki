import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME

def check_table():
    db = StockDBManager()
    if db.connect():
        try:
            with db.conn.cursor() as cur:
                # 스키마 내 테이블 목록 조회
                sql = f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = '{SCHEMA_NAME}'
                    AND table_type = 'BASE TABLE';
                """
                cur.execute(sql)
                tables = [row[0] for row in cur.fetchall()]
                
                print(f"Schema: {SCHEMA_NAME}")
                print(f"Tables: {tables}")
                
                if 'stock_recommendation_history' in tables:
                    print("✅ stock_recommendation_history 테이블이 존재합니다.")
                    
                    # 컬럼 확인
                    cur.execute(f"""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_schema = '{SCHEMA_NAME}' 
                        AND table_name = 'stock_recommendation_history';
                    """)
                    columns = cur.fetchall()
                    print("Columns:", columns)
                else:
                    print("❌ stock_recommendation_history 테이블이 존재하지 않습니다.")
                    
        except Exception as e:
            print(f"확인 중 오류 발생: {e}")
        finally:
            db.disconnect()
    else:
        print("DB 연결 실패")

if __name__ == "__main__":
    check_table()
