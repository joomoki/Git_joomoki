import sys
import os
import pandas as pd
from datetime import datetime
import time

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.db_config import DB_CONFIG, SCHEMA_NAME
from src.stock_db_manager import StockDBManager
from src.analysis.indicators import analyze_stock

def run_daily_analysis():
    print("=== 전종목 일일 기술적 분석 시작 ===")
    
    db_manager = StockDBManager()
    if not db_manager.connect():
        print("DB 연결 실패")
        return

    try:
        # 1. 분석 대상 종목 가져오기
        stocks = db_manager.get_all_stocks()
        total_stocks = len(stocks)
        print(f"총 {total_stocks}개 종목 분석 시작")

        today = datetime.now().strftime('%Y-%m-%d')
        success_count = 0
        
        for i, (stock_code, market_type, company_name) in enumerate(stocks):
            if i % 100 == 0:
                print(f"[{i}/{total_stocks}] 진행 중... (완료: {success_count})")

            try:
                # 2. 최근 데이터 조회 (60일치면 충분)
                with db_manager.conn.cursor() as cur:
                    cur.execute(f"""
                        SELECT trade_date, open_price, high_price, low_price, close_price, volume 
                        FROM {SCHEMA_NAME}.stock_prices 
                        WHERE stock_code = %s 
                        ORDER BY trade_date DESC 
                        LIMIT 60
                    """, (stock_code,))
                    rows = cur.fetchall()
                
                if not rows or len(rows) < 20: # 데이터 너무 적으면 패스
                    continue
                    
                # 시간 역순으로 가져왔으니 다시 정렬
                rows.reverse()
                df = pd.DataFrame(rows, columns=['trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'])
                
                # 3. 분석 수행
                result = analyze_stock(df)
                
                if result.get('status') == '데이터 부족':
                    continue
                    
                # 4. 분석 결과 저장
                analysis_data = {
                    'date': today, # 오늘 날짜 기준 분석 (실제 데이터 날짜와 다를 수 있음 주의)
                    # 실제로는 df['trade_date'].iloc[-1] 을 쓰는 게 더 정확할 수 있음.
                    # 여기서는 '분석을 수행한 날짜'로 기록.
                    'summary': result['summary'],
                    'score': result['score'],
                    'confidence': 0.8 # 임시 값
                }
                
                # 실제 데이터의 최신 날짜로 덮어쓰기 (중복 분석 방지)
                last_trade_date = df['trade_date'].iloc[-1]
                if isinstance(last_trade_date, str):
                    analysis_data['date'] = last_trade_date
                else:
                    analysis_data['date'] = last_trade_date.strftime('%Y-%m-%d')

                if db_manager.save_analysis_result(stock_code, analysis_data):
                    success_count += 1
                    
            except Exception as e:
                print(f"분석 실패 ({stock_code}): {e}")
                db_manager.conn.rollback() # 롤백 중요

        print(f"\n[완료] 총 {success_count}개 종목 분석 및 저장 완료")

    except Exception as e:
        print(f"치명적 오류: {e}")
    finally:
        db_manager.disconnect()

if __name__ == "__main__":
    run_daily_analysis()
