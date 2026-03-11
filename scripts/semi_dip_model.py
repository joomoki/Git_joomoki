#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
반도체 지수 급락 시 '줍줍' 모델 (과매도 반등 중심)
- SOXX ETF (SOX 지수 추종)로 5거래일 내 7% 이상 하락 감지
- RSI 30 이하 과매도 국내 반도체 종목 추출
- 과거 유사 급락 시점에서의 평균 반등 백테스트
"""

import sys
import os
import json
import math
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("[WARN] yfinance 없음. pip install yfinance")

from src.stock_db_manager import StockDBManager

# ─────────────────────────────────────
# SOX 대리 지수
# ─────────────────────────────────────
SOX_TICKER = "SOXX"   # iShares Semiconductor ETF (SOX 추종)
SOX_DROP_THRESHOLD = -7.0   # 5거래일 낙폭 트리거 (%)
RSI_OVERSOLD = 30            # RSI 과매도 기준

# 국내 반도체 종목 직접 코드 목록
KR_SEMI_CODES = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "042700",  # 한미반도체
    "019870",  # 삼성SDI (관련)
    "078020",  # 이루온
    "091120",  # 이엔에프테크놀로지
    "036830",  # 솔브레인홀딩스
    "058470",  # 리노공업
    "039030",  # 이오테크닉스
    "122870",  # 와이씨
    "095340",  # ISC
    "036490",  # SK하이닉스 (ASSC)
    "030530",  # 원익IPS
    "104830",  # 워트
    "053270",  # 피에스케이홀딩스
]

# 반도체 섹터 키워드 (DB 검색용)
SEMI_KEYWORDS = ["반도체", "semiconductor", "팹", "fab", "웨이퍼", "DRAM", "낸드", "HBM",
                 "파운드리", "메모리", "칩", "집적회로"]


def fetch_sox_data(period_days=90):
    """SOXX ETF 가격 데이터 수집."""
    if not HAS_YFINANCE:
        return []
    try:
        end = datetime.date.today()
        start = end - datetime.timedelta(days=period_days)
        df = yf.download(SOX_TICKER, start=start.isoformat(), end=end.isoformat(),
                         interval="1d", progress=False, auto_adjust=True)
        if df is None or df.empty:
            return []
        result = []
        for idx, row in df.iterrows():
            close_val = row["Close"]
            close_val = float(close_val.iloc[0]) if hasattr(close_val, "iloc") else float(close_val)
            result.append({
                "date": idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10],
                "close": close_val
            })
        return result
    except Exception as e:
        print(f"    [WARN] SOXX 수집 실패: {e}")
        return []


def compute_rsi(prices_list, period=14):
    """
    RSI 계산 (Wilder 방식 근사).
    prices_list: [close 값] 리스트
    """
    if len(prices_list) < period + 1:
        return 50.0

    gains = []
    losses = []
    for i in range(1, len(prices_list)):
        diff = prices_list[i] - prices_list[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))

    # 초기 평균
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Wilder 평활
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def analyze_sox(sox_prices):
    """SOX 5거래일 낙폭 분석."""
    if len(sox_prices) < 6:
        return {
            "latest_price": None,
            "drop_5d_pct": None,
            "triggered": False,
            "trigger_level": "NONE",
            "price_history": []
        }

    latest = sox_prices[-1]["close"]
    five_days_ago = sox_prices[-6]["close"]
    drop_pct = (latest - five_days_ago) / five_days_ago * 100

    triggered = drop_pct <= SOX_DROP_THRESHOLD

    if drop_pct <= -15:
        level = "EXTREME"
    elif drop_pct <= -10:
        level = "HIGH"
    elif drop_pct <= SOX_DROP_THRESHOLD:
        level = "MODERATE"
    else:
        level = "NONE"

    print(f"    SOXX 5일 낙폭: {drop_pct:.2f}% → {level}{' [TRIGGERED]' if triggered else ''}")

    return {
        "latest_price": round(latest, 4),
        "five_days_ago_price": round(five_days_ago, 4),
        "drop_5d_pct": round(drop_pct, 4),
        "triggered": triggered,
        "trigger_level": level,
        "threshold_pct": SOX_DROP_THRESHOLD,
        "price_history": sox_prices[-30:]
    }


def get_oversold_semis(db, sox_analysis):
    """RSI 과매도 국내 반도체 종목 추출 및 백테스트."""
    print("  [SEMI] 국내 반도체 RSI 분석 중...")
    stocks = db.get_market_stocks(limit=None, sort_by='ai_score')
    if not stocks:
        return [], []

    stock_map = {s[0]: s for s in stocks}

    # 반도체 종목 필터
    semi_stocks = []
    for s in stocks:
        sector_val = (s[3] or "").lower()
        name_val = (s[1] or "").lower()
        combined = sector_val + " " + name_val
        if s[0] in KR_SEMI_CODES or any(kw.lower() in combined for kw in SEMI_KEYWORDS):
            semi_stocks.append(s)

    if not semi_stocks:
        print("    [WARN] 반도체 종목 미발견, KR_SEMI_CODES 직접 사용")
        semi_stocks = [stock_map[c] for c in KR_SEMI_CODES if c in stock_map]

    results = []
    backtest_data = []

    for s in semi_stocks:
        code = s[0]
        name = s[1]
        price = float(s[4]) if s[4] else 0
        ai_score = int(s[21]) if len(s) > 21 and s[21] else 0

        # chart_data 찾기 (인덱스로 접근)
        # 구조: (code, name, market, sector, price, ..., chart_data_idx)
        # get_market_stocks에서 반환하는 구조를 따름
        chart_data_raw = s[22] if len(s) > 22 else None

        # chart_data가 없으면 RSI 계산 불가 → 스킵하지 않고 RSI=None으로 표시
        rsi = None
        prices_close = []
        max_drawdown = None
        backtest_avg_return = None

        if chart_data_raw and isinstance(chart_data_raw, list):
            prices_close = [d["close"] for d in chart_data_raw if "close" in d]
        elif chart_data_raw and isinstance(chart_data_raw, str):
            try:
                chart_list = json.loads(chart_data_raw)
                prices_close = [d.get("close", 0) for d in chart_list]
            except Exception:
                prices_close = []

        if len(prices_close) >= 15:
            rsi = compute_rsi(prices_close, period=14)

            # 최대 낙폭 (MDD) 계산
            peak = prices_close[0]
            max_dd = 0.0
            for p in prices_close:
                peak = max(peak, p)
                dd = (peak - p) / peak * 100 if peak > 0 else 0
                max_dd = max(max_dd, dd)
            max_drawdown = round(max_dd, 2)

            # === 간단 백테스트 ===
            # 과거 데이터 내에서 SOX 급락과 유사한 하락 구간 찾아 반등 계산
            window = 5   # 매수 신호 후 보유 기간(거래일)
            bt_returns = []
            for i in range(10, len(prices_close) - window):
                seg = prices_close[i-5:i]
                if not seg:
                    continue
                seg_drop = (seg[-1] - seg[0]) / seg[0] * 100 if seg[0] > 0 else 0
                # 유사 조건: 5일 내 5% 이상 하락 시점
                if seg_drop <= -5:
                    buy_price = prices_close[i]
                    sell_price = prices_close[i + window]
                    ret = (sell_price - buy_price) / buy_price * 100 if buy_price > 0 else 0
                    bt_returns.append(round(ret, 2))

            backtest_avg_return = round(sum(bt_returns) / len(bt_returns), 2) if bt_returns else None
            bt_win_rate = round(sum(1 for r in bt_returns if r > 0) / len(bt_returns) * 100, 1) if bt_returns else None

            if backtest_avg_return is not None:
                backtest_data.append({
                    "code": code,
                    "name": name,
                    "avg_return_pct": backtest_avg_return,
                    "win_rate_pct": bt_win_rate,
                    "sample_count": len(bt_returns),
                    "holding_days": window
                })
        else:
            bt_win_rate = None

        oversold = rsi is not None and rsi <= RSI_OVERSOLD
        # SOX 급락 미발동 시에도 RSI 상위(낮은 값) 종목 표시
        # 발굴 점수: AI점수 베이스 + RSI 낮을수록 점수 높음 + SOX 트리거 추가점
        score = ai_score
        if rsi is not None:
            rsi_bonus = max(0, (RSI_OVERSOLD - rsi) * 1.5) if rsi <= 50 else 0
            score += rsi_bonus
        if sox_analysis.get("triggered"):
            score += 15

        results.append({
            "code": code,
            "name": name,
            "market": s[2],
            "sector": s[3],
            "price": price,
            "ai_score": ai_score,
            "rsi": rsi,
            "oversold": oversold,
            "max_drawdown": max_drawdown,
            "backtest_avg_return": backtest_avg_return,
            "backtest_win_rate": bt_win_rate,
            "discovery_score": round(min(score, 100), 1)
        })

    # RSI 낮은 순 (과매도 먼저) 정렬
    results.sort(key=lambda x: (x["rsi"] is None, x["rsi"] if x["rsi"] is not None else 999))
    top_results = results[:10]
    backtest_data.sort(key=lambda x: x.get("avg_return_pct", 0), reverse=True)

    oversold_count = sum(1 for r in top_results if r.get("oversold"))
    print(f"    - {len(top_results)}개 반도체 종목 분석 완료 (과매도 {oversold_count}개, RSI < {RSI_OVERSOLD})")
    return top_results, backtest_data[:10]


def build_and_save(sox_analysis, oversold_stocks, backtest_data):
    """결과를 JS 파일로 저장."""
    data = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "sox_analysis": sox_analysis,
        "oversold_stocks": oversold_stocks,
        "backtest_summary": backtest_data,
        "drop_threshold_pct": SOX_DROP_THRESHOLD,
        "rsi_oversold_level": RSI_OVERSOLD,
        "model_description": (
            f"SOXX ETF(SOX 대리 지수) 5거래일 낙폭이 {abs(SOX_DROP_THRESHOLD)}% 이상일 때 "
            f"RSI {RSI_OVERSOLD} 이하 국내 반도체 과매도 종목을 발굴하는 모델입니다."
        )
    }
    output_dir = os.path.join("D:\\", "joomoki_PJ", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "semi_dip_data.js")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"const semiDipData = {json.dumps(data, ensure_ascii=False, default=str)};")
    print(f"  [SEMI] 저장 완료: {output_path}")
    return output_path


def run():
    """SOX 급락 줍줍 모델 실행 진입점."""
    print("\n=== 반도체 SOX 급락 줍줍 모델 실행 ===")
    if not HAS_YFINANCE:
        print("[ERROR] yfinance 미설치. pip install yfinance")
        return

    # 1. SOXX 데이터 수집
    print("  [SEMI] SOXX ETF 데이터 수집...")
    sox_prices = fetch_sox_data(period_days=90)
    sox_analysis = analyze_sox(sox_prices)

    if sox_analysis["triggered"]:
        print(f"  [TRIGGERED] SOX 5일 낙폭 {sox_analysis['drop_5d_pct']:.2f}% → 줍줍 경보 발동!")
    else:
        pct = sox_analysis.get("drop_5d_pct")
        if pct is not None:
            print(f"  [OK] 현재 5일 낙폭 {pct:.2f}% (기준 {SOX_DROP_THRESHOLD}% 미달). 과매도 종목 모니터링 유지.")
        else:
            print("  [OK] 데이터 불충분. 과매도 종목 모니터링 유지.")

    # 2. DB에서 반도체 종목 RSI 분석
    db = StockDBManager()
    oversold_stocks = []
    backtest_data = []
    if db.connect():
        try:
            result = get_oversold_semis(db, sox_analysis)
            if isinstance(result, tuple):
                oversold_stocks, backtest_data = result
            else:
                oversold_stocks = result
        finally:
            db.disconnect()
    else:
        print("  [WARN] DB 연결 실패")

    # 3. 저장
    build_and_save(sox_analysis, oversold_stocks, backtest_data)
    print("=== 완료 ===\n")


if __name__ == "__main__":
    run()
