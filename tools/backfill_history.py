import sys
import os
import datetime
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager
from src.export_to_web import calculate_and_save_korea_scores, calculate_and_save_us_scores, save_history

def backfill_history():
    print("[INFO] Starting 7-day Backfill...")
    db = StockDBManager()
    if not db.connect():
        print("[ERROR] DB Connection Failed")
        return

    # 최근 10일 중 데이터가 있는 날짜 7개 정도 확보 (주말 고려)
    # 2026-02-09 부터 명시적으로 포함 (요청사항 반영)
    today = datetime.datetime.now().date()
    
    target_dates = []
    
    # 2월 9일부터 오늘까지 루프
    start_dt = datetime.date(2026, 2, 9)
    delta = (today - start_dt).days
    
    for i in range(delta + 1):
        d = start_dt + timedelta(days=i)
        if d.weekday() < 5:
            target_dates.append(d.strftime("%Y-%m-%d"))
    
    # 과거 날짜부터 처리 (오래된 순)
    target_dates.sort()
    
    print(f"Target Dates: {target_dates}")

    processed_count = 0
    for date_str in target_dates:
        print(f"\n[Processing Date: {date_str}]")
        
        # 1. AI 점수 재계산 (과거 시점 기준)
        calculate_and_save_korea_scores(db, target_date=date_str)
        calculate_and_save_us_scores(db, target_date=date_str)
        
        # 2. 데이터 조회
        # get_market_stocks sort_by='prediction' uses 'UP' first
        korea_stocks = db.get_market_stocks(limit=None, target_date=date_str, sort_by='prediction')
        us_stocks = db.get_us_market_stocks(limit=None, target_date=date_str, sort_by='prediction')
        
        # 데이터가 거의 없으면 스킵 (휴장일 등)
        if len(korea_stocks) < 1 and len(us_stocks) < 1:
            print(f"  - No sufficient data for {date_str}. Skipping.")
            continue
            
        # 3. Top Picks Selection (Top 6 KR, Top 6 US)
        # Korea Formatting & Selection
        formatted_korea = []
        for s in korea_stocks:
            # 0:code, 4:price, 8:prediction, 11:m_cap, 21:score, 22:chart_data
            chart_data = s[22] if (len(s) > 22 and s[22]) else []
            score = s[21] if (len(s) > 21 and s[21] is not None) else 0
            
            # Simple Filter: Score >= 50 (loosened for backfill)
            if score >= 50:
                formatted_korea.append({
                    'code': s[0],
                    'price': float(s[4]) if s[4] else 0,
                    'analysis': {
                        'prediction': s[8],
                        'score': score
                    },
                    'financials': {
                        'market_cap': float(s[11]) if s[11] else 0
                    },
                    'chart_data': chart_data,
                    'is_us': False
                })
        
        # Sort KR: Score DESC, Market Cap DESC
        formatted_korea.sort(key=lambda x: (x['analysis']['score'], x['financials']['market_cap']), reverse=True)
        top_korea = formatted_korea[:6]
            
        # US Formatting & Selection
        formatted_us = []
        for s in us_stocks:
             # 0:code, 5:price, 9:prediction, 12:score, 13:m_cap, 14:price_history
             chart_data = s[14] if (len(s) > 14 and s[14]) else []
             score = s[12] if (len(s) > 12 and s[12] is not None) else 0
             
             if score >= 50:
                 formatted_us.append({
                    'code': s[0],
                    'price': float(s[5]) if s[5] else 0,
                    'analysis': {
                        'prediction': s[9],
                        'score': score
                    },
                    'financials': {
                        'market_cap': float(s[13]) if s[13] else 0
                    },
                    'chart_data': chart_data,
                    'is_us': True
                })

        # Sort US: Score DESC, Market Cap DESC
        formatted_us.sort(key=lambda x: (x['analysis']['score'], x['financials']['market_cap']), reverse=True)
        top_us = formatted_us[:6]

        # 4. 추천 이력 저장
        save_history(db, top_korea, top_us, target_date=date_str)
        processed_count += 1

    # 마지막에 히스토리 데이터 파일 생성
    from src.export_to_web import export_history_data
    # data_dir path calculation
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_portal_joomoki', 'data')
    export_history_data(db, data_dir)
    
    db.disconnect()
    print("\n[Backfill Completed]")

if __name__ == "__main__":
    backfill_history()
