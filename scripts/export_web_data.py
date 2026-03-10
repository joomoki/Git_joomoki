import sys
import os
import json
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager

def export_data():
    print("=== 웹 포털용 데이터 추출 시작 (전 종목) ===")
    
    db = StockDBManager()
    if not db.connect():
        print("DB 연결 실패")
        return

    try:
        # 1. 전 종목 데이터 가져오기 (Limit 제거)
        # get_market_stocks 쿼리가 수정되어 인덱스가 변경되었으므로 주의
        # 0:code, 1:name, 2:market, 3:sector, 4:close, 5:vol, 6:date, 
        # 7:summary, 8:pred, 9:per, 10:pbr, 11:cap, 12:eps, 13:bps
        # 14:sales, 15:op_prof, 16:debt, 17:frgn_buy, 18:pgm_buy
        # 19:price_hist, 20:frgn_trend, 21:inst_trend
        
        rows = db.get_market_stocks(limit=None, sort_by='market_cap')
        
        stocks_data = []
        top_picks = []
        
        print(f"총 {len(rows)}개 종목 데이터 처리 중...")
        
        for i, row in enumerate(rows):
            stock_code = row[0]
            company_name = row[1]
            market_type = row[2]
            sector = row[3]
            curr_price = row[4]
            # ... 인덱스 매핑이 복잡하므로 변수로 명확히
            
            # DB 조회로 상세 차트 데이터 (최근 60일)
            # 전 종목 루프 돌면 시간이 좀 걸리지만 로컬 DB라 할만함
            daily_prices = db.get_daily_prices(stock_code, limit=60)
            
            chart_data = []
            if daily_prices:
                for p in daily_prices:
                    # p: trade_date, open, high, low, close, volume (tuple)
                    chart_data.append({
                        'date': str(p[0]),
                        'close': p[4]
                    })
            
            # 수급 추이 (이미 쿼리에서 배열로 가져왔음 - 최근 20일)
            # row[20]: foreigner_trend, row[21]: institution_trend
            # 하지만 날짜가 없어서 차트에 못 그림.
            # 일단 sparkline용으로만 쓰거나, daily_prices 날짜와 매핑?
            # investor_trend 상세 데이터도 DB에서 가져오려면 get_investor_trends_history 필요.
            # 여기선 쿼리에서 가져온 배열을 그대로 사용하자 (순서는 trade_date DESC -> 스크립트에서 ASC 정렬 필요? 쿼리에서 ASC 했나? 쿼리에서 ORDER BY trade_date ASC 했음)
            
            def to_list(pg_array):
                return pg_array if pg_array is not None else []

            stock_info = {
                'code': stock_code,
                'name': company_name,
                'market': market_type,
                'sector': sector or 'Unknown',
                'price': curr_price,
                'volume': row[5],
                'date': str(row[6]),
                'analysis': {
                    'summary': row[7],
                    'prediction': row[8],
                },
                'financials': {
                    'per': row[9],
                    'pbr': row[10],
                    'market_cap': row[11], # 시총
                    'eps': row[12],
                    'bps': row[13],
                    'sales': row[14],
                    'op_profit': row[15],
                    'debt_ratio': row[16]
                },
                'investor': {
                    'frgn_net_buy': row[17], # 최신 1일
                    'pgm_net_buy': row[18],  # 최신 1일
                    'frgn_trend': to_list(row[20]), # 배열
                    'inst_trend': to_list(row[21])  # 배열
                },
                'chart_data': chart_data # 상세 차트용
            }
            
            stocks_data.append(stock_info)
            
            # 추천 종목 선정
            if row[8] == 'UP':
                top_picks.append(stock_info)
                
            if (i+1) % 500 == 0:
                print(f"{i+1}개 처리 완료...")
        
        # 2. JSON 구조 생성
        output_data = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_stocks': len(stocks_data),
            'top_picks': top_picks, 
            'stocks': stocks_data 
        }
        
        # 3. 파일 저장
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'stock_portal_joomoki', 'data')
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, 'stock_data.js')
        
        from decimal import Decimal
        class DecimalEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                return super(DecimalEncoder, self).default(obj)

        json_str = json.dumps(output_data, ensure_ascii=False, indent=2, cls=DecimalEncoder)
        js_content = f"const stockData = {json_str};"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
            
        print(f"데이터 저장 완료: {output_file}")
        print(f"- 전체 종목: {len(stocks_data)}개")
            
    except Exception as e:
        print(f"데이터 추출 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.disconnect()

if __name__ == "__main__":
    export_data()
