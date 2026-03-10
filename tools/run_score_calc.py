import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager
from src.export_to_web import calculate_and_save_korea_scores, save_history

def run_score_calc():
    print("=== Run Score Calculation (Feb 19) ===")
    
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        target_date = '2026-02-19'
        
        # 1. Calculate Scores
        calculate_and_save_korea_scores(db, target_date=target_date)
        
        # save_history는 top_korea, top_us를 인자로 받도록 수정됨
        # 해당 스크립트는 단순히 테스트용이므로 에러가 나지 않게 빈 리스트를 전달하여 실행되게 함
        # 실제 점수는 export_to_web 내에 저장됨
        from src.export_to_web import save_history
        save_history(db, [], [], target_date=target_date)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()
        print("=== Completed ===")

if __name__ == "__main__":
    run_score_calc()
