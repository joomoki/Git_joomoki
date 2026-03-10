
from stock_db_manager import StockDBManager

def list_tables():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        with db.conn.cursor() as cur:
            sql = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'stock_portal'
                ORDER BY table_name;
            """
            cur.execute(sql)
            rows = cur.fetchall()
            
            print("\n[Tables in stock_portal]")
            for r in rows:
                print(r[0])
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    list_tables()
