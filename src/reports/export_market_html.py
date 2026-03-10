
import sys
import os
import datetime
from jinja2 import Environment, FileSystemLoader

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_db_manager import StockDBManager

def export_market_report():
    print("시장 현황 리포트 생성 시작...")
    
    # 1. DB 연결 및 데이터 조회
    db = StockDBManager()
    if not db.connect():
        print("DB 연결 실패")
        return

    raw_data = db.get_market_overview()
    db.disconnect()
    
    if not raw_data:
        print("데이터가 없습니다.")
        return

    # 2. 데이터 가공 (market.html 템플릿과 동일한 구조로 변환)
    stocks = []
    for row in raw_data:
        # row: (stock_code, company_name, market_type, sector, close_price, volume, analysis_summary, price_prediction, per, pbr, market_cap)
        # 튜플 인덱스는 쿼리 순서에 따름
        stock = {
            'code': row[0],
            'name': row[1],
            'market': row[2],
            'sector': row[3],
            'close': int(row[4]) if row[4] else 0,
            'volume': row[5],
            'summary': row[6],
            'prediction': row[7],
            'per': row[8],
            'pbr': row[9],
            'market_cap': row[10]
        }
        stocks.append(stock)

    today = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 3. Jinja2 템플릿 로드
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'web', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('market.html')

    # 4. 렌더링
    # 주의: market.html에 있는 onclick 링크(/stock/...)는 정적 파일에서 동작하지 않거나 웹 서버가 필요함.
    # 완전한 정적 파일로 만들려면 링크를 제거하거나 절대 경로로 바꿔야 하지만, 
    # 일단은 뷰(View) 전용이므로 그대로 둠.
    
    html_content = template.render(stocks=stocks, today=today)
    
    # 추가: 모바일에서 보기 편하게 일부 스타일 강제 주입 (필요시)
    # 이미 market.html이 반응형이라 크게 필요 없을 수 있음.

    # 5. 파일 저장
    filename = f"market_report_{datetime.datetime.now().strftime('%Y%m%d')}.html"
    # 프로젝트 루트에 저장
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"리포트 생성 완료: {output_path}")

if __name__ == "__main__":
    export_market_report()
