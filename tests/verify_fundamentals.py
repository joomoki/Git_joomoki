
import sys
import os
import unittest
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager, SCHEMA_NAME

class VerifyFundamentals(unittest.TestCase):
    def setUp(self):
        self.db_manager = StockDBManager()
        self.db_manager.connect()

    def tearDown(self):
        self.db_manager.disconnect()

    def test_recent_data(self):
        """Check if recent fundamental data exists (Today and Yesterday for backfill)"""
        dates_to_check = [
            datetime.now().strftime('%Y-%m-%d'), 
            (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        ]
        
        for check_date in dates_to_check:
            print(f"\nChecking data for date: {check_date}")
            try:
                with self.db_manager.conn.cursor() as cur:
                    sql = f"SELECT COUNT(*) FROM {SCHEMA_NAME}.stock_fundamentals WHERE base_date = %s"
                    cur.execute(sql, (check_date,))
                    count = cur.fetchone()[0]
                    print(f"Count of fundamentals for {check_date}: {count}")
                    
                    if count > 0:
                        print(f"Data found for {check_date}!")
                    else:
                        print(f"No data found for {check_date}.")
                    
                    # Check a specific stock, e.g., Samsung Electronics
                    sql = f"SELECT * FROM {SCHEMA_NAME}.stock_fundamentals WHERE stock_code = '005930' AND base_date = %s"
                    cur.execute(sql, (check_date,))
                    row = cur.fetchone()
                    if row:
                        print(f"Samsung Electronics (005930) Data: Found")
                    else:
                        print(f"Samsung Electronics (005930) Data: Not Found")

            except Exception as e:
                print(f"DB Error: {e}")

if __name__ == "__main__":
    unittest.main()
