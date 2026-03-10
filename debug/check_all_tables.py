
from stock_db_manager import StockDBManager

def list_all_tables():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        with db.conn.cursor() as cur:
            # 모든 스키마의 테이블 조회 (시스템 스키마 제외)
            sql = """
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                ORDER BY table_schema, table_name;
            """
            cur.execute(sql)
            rows = cur.fetchall()
            
            print("\n[All Tables]")
            for r in rows:
                print(f"{r[0]}.{r[1]}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    list_all_tables()
