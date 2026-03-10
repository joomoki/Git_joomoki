from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
import uvicorn
import sys
import os
import pandas as pd
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.stock_db_manager import StockDBManager
from src.analysis.indicators import analyze_stock

app = FastAPI(title="Joomoki Stock Dashboard")

# 정적 파일 및 템플릿 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

db_manager = StockDBManager()

@app.on_event("startup")
def startup():
    db_manager.connect()

@app.on_event("shutdown")
def shutdown():
    db_manager.disconnect()

@app.get("/")
def read_root(request: Request):
    return RedirectResponse(url="/market")

@app.get("/search")
def search_stock(q: str):
    """
    종목 검색 API (자동완성 등 활용 가능)
    """
    if not q:
        return []
    
    # DB에서 종목 검색 (간단히 구현)
    # 실제로는 Like 검색 쿼리 필요. 현재 StockDBManager에는 전체 조회만 있음.
    # 임시로 전체 조회 후 필터링 (데이터 많으면 성능 이슈 가능, 추후 쿼리로 변경 권장)
    all_stocks = db_manager.search_stocks(q)
    results = []
    for code, market, name in all_stocks:
        results.append({"code": code, "name": name, "market": market})
    return results

@app.get("/stock/{code}")
def stock_dashboard(request: Request, code: str):
    """
    주식 대시보드 페이지
    """
    try:
        # 1. 종목 정보 조회
        stock_info = db_manager.get_stock_info(code)
        
        if not stock_info:
            raise HTTPException(status_code=404, detail="Unknown Stock Code")
            
        code, market, name = stock_info

        # 2. 주가 데이터 조회 (최근 1년)
        rows = db_manager.get_daily_prices(code, limit=365)
            
        if not rows:
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "stock": {"code": code, "name": name, "market": market},
                "error": "데이터가 없습니다."
            })

        # DataFrame 변환
        df = pd.DataFrame(rows, columns=['trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'])
        
        # Decimal -> float/int 변환 (pandas_ta 호환성)
        numeric_cols = ['open_price', 'high_price', 'low_price', 'close_price']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)

        # 3. 기술적 분석 수행
        analysis_result = analyze_stock(df)
        
        # 4. 템플릿 렌더링
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "stock": {"code": code, "name": name, "market": market},
            "analysis": analysis_result,
            "last_updated": df['trade_date'].iloc[-1] if not df.empty else "-"
        })

    except Exception as e:
        print(f"Dashboard Error: {e}")
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)})

@app.get("/market")
def market_overview(request: Request, page: int = 1, sort: str = "market_cap"):
    """
    시장 전체 분석 리스트 (페이징/정렬)
    """
    try:
        limit = 30
        overview_data = db_manager.get_market_stocks(page=page, limit=limit, sort_by=sort)
        total_count = db_manager.get_market_stock_count()
        total_pages = (total_count + limit - 1) // limit
        
        # 튜플 -> 딕셔너리 변환 (get_market_stocks 구조에 맞춤)
        stocks = []
        for row in overview_data:
            stocks.append({
                "code": row[0],
                "name": row[1],
                "market": row[2],
                "sector": row[3],
                "close": row[4],
                "volume": row[5],
                # row[6] is trade_date
                "summary": row[7],
                "prediction": row[8],
                "per": row[9],
                "pbr": row[10],
                "market_cap": row[11],
                "price_history": row[14] # sparkline data if needed
            })
            
        return templates.TemplateResponse("market.html", {
            "request": request, 
            "stocks": stocks,
            "today": datetime.now().strftime('%Y-%m-%d'),
            "page": page,
            "total_pages": total_pages,
            "sort": sort
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)})

@app.get("/api/stock/{code}/history")
def stock_history(code: str):
    """
    차트용 데이터 API
    """
    rows = db_manager.get_daily_prices(code, limit=365)
        
    data = []
    for r in rows:
        data.append({
            "time": r[0].strftime("%Y-%m-%d"),
            "open": float(r[1]),
            "high": float(r[2]),
            "low": float(r[3]),
            "close": float(r[4]),
            "volume": int(r[5])
        })
    return data

@app.get("/screener")
def screener(request: Request):
    """
    주식 스크리너 페이지
    """
    return templates.TemplateResponse("screener.html", {"request": request})

@app.post("/api/screener")
async def api_screener(request: Request):
    """
    스크리너 필터링 API
    """
    try:
        data = await request.json()
        
        # 필터링 조건 구성
        criteria = {
            'min_per': float(data.get('min_per')) if data.get('min_per') else None,
            'max_per': float(data.get('max_per')) if data.get('max_per') else None,
            'min_pbr': float(data.get('min_pbr')) if data.get('min_pbr') else None,
            'max_pbr': float(data.get('max_pbr')) if data.get('max_pbr') else None,
            'min_market_cap': int(data.get('min_market_cap')) if data.get('min_market_cap') else None,
            'trend': data.get('trend') if data.get('trend') != 'ALL' else None
        }
        
        results = db_manager.get_filtered_stocks(criteria)
        
        stocks = []
        for row in results:
            stocks.append({
                "code": row[0],
                "name": row[1],
                "market": row[2],
                "sector": row[3],
                "close": row[4],
                "volume": row[5],
                "summary": row[6],
                "prediction": row[7],
                "per": row[8],
                "pbr": row[9],
                "market_cap": row[10],
                "signals": row[11] if len(row) > 11 else []
            })
            
        return stocks
    except Exception as e:
        print(f"Screener API Error: {e}")
        return []

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
