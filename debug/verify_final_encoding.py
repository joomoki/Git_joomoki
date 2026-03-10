
import sys
import os
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME

def verify():
    db = StockDBManager()
    db.connect()
    
    with db.conn.cursor() as cur:
        # Get 5 random stocks with descriptions
        cur.execute(f"SELECT stock_code, company_name, description FROM {SCHEMA_NAME}.stock_companies WHERE description IS NOT NULL ORDER BY RANDOM() LIMIT 5")
        rows = cur.fetchall()
        
        print(f"Checking {len(rows)} random stocks...")
        for row in rows:
            code, name, desc = row
            print(f"[{code}] {name}")
            print(f"Desc Sample: {desc[:60]}...")
            print("-" * 40)
            
    db.disconnect()

if __name__ == "__main__":
    verify()
