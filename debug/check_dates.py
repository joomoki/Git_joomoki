import psycopg2
from config.db_config import DB_CONFIG, SCHEMA_NAME

def main():
    conn=psycopg2.connect(**DB_CONFIG)
    cur=conn.cursor()
    
    print('--- KOREA (daily_price) 2026-02-20 ---')
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.daily_price WHERE trade_date = '2026-02-20'")
    print(cur.fetchone())
    
    cur.execute(f"SELECT trade_date, COUNT(*) FROM {SCHEMA_NAME}.daily_price GROUP BY trade_date ORDER BY trade_date DESC LIMIT 5")
    kr_dates = cur.fetchall()
    print('최근 KR 날짜 5개:', kr_dates)
    
    print('\n--- US (us_stock_prices) 2026-02-20 ---')
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.us_stock_prices WHERE trade_date = '2026-02-20'")
    print(cur.fetchone())
    
    cur.execute(f"SELECT trade_date, COUNT(*) FROM {SCHEMA_NAME}.us_stock_prices GROUP BY trade_date ORDER BY trade_date DESC LIMIT 5")
    us_dates = cur.fetchall()
    print('최근 US 날짜 5개:', us_dates)

    conn.close()

if __name__ == '__main__':
    main()
