#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전쟁/지정학적 리스크 모델
WTI 유가, 금 선물, 방산 ETF(ITA) 변동성을 감지하여
수혜가 예상되는 국내 종목을 발굴합니다.
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
    print("[WARN] yfinance가 없습니다. pip install yfinance 로 설치해주세요.")

from src.stock_db_manager import StockDBManager

# ─────────────────────────────────────────
# 감시 자산 정의
# ─────────────────────────────────────────
WATCH_ASSETS = {
    "WTI":  {"ticker": "CL=F",  "name": "WTI 원유 선물",        "icon": "🛢️"},
    "GOLD": {"ticker": "GC=F",  "name": "금 선물",              "icon": "🪙"},
    "ITA":  {"ticker": "ITA",   "name": "미 방산 ETF(ITA)",     "icon": "🛡️"},
}

# 변동성 윈도우 (거래일 기준)
LOOKBACK_DAYS = 20  # μ, σ 계산에 사용하는 최근 거래일 수
SIGMA_THRESHOLD = 2.0

# ─────────────────────────────────────────
# 수혜 섹터 및 대표 종목 (섹터 키워드 기반)
# ─────────────────────────────────────────
BENEFICIARY_SECTORS = {
    "방산": {
        "keywords": ["방산", "항공", "방위", "무기", "군수", "레이더", "탄약"],
        "icon": "🛡️",
        "reason": "전쟁 발생 시 방산 수요 급증",
        "risk_types": ["WAR", "CONFLICT"]
    },
    "에너지": {
        "keywords": ["정유", "에너지", "석유", "가스", "화학"],
        "icon": "⚡",
        "reason": "유가 상승 시 정유·에너지 기업 수혜",
        "risk_types": ["OIL_SPIKE"]
    },
    "해운·물류": {
        "keywords": ["해운", "선박", "운송", "물류", "항만", "컨테이너"],
        "icon": "🚢",
        "reason": "공급망 혼란 시 해운 운임 급등",
        "risk_types": ["OIL_SPIKE", "WAR"]
    },
    "소재·광물": {
        "keywords": ["철강", "금속", "광업", "귀금속", "희소금속", "구리", "니켈"],
        "icon": "⛏️",
        "reason": "안전자산 금 상승 및 원자재 수급 불안",
        "risk_types": ["GOLD_SPIKE"]
    }
}

# 직접 매핑 종목 코드 (섹터 키워드 미탐지 보완용)
DIRECT_MAPPING = {
    "방산": ["012450", "047810", "064350", "272210", "079550", "278280", "105840", "014570"],
    "에너지": ["096770", "010950", "078930", "267250", "011070"],
    "해운·물류": ["011200", "028670", "088350", "00554K"],
    "소재·광물": ["005490", "010130", "024900", "009830"]
}


def fetch_asset_data(ticker, period_days=35):
    """yfinance로 자산 가격 데이터를 가져옵니다."""
    if not HAS_YFINANCE:
        return []
    try:
        end = datetime.date.today()
        start = end - datetime.timedelta(days=period_days)
        df = yf.download(ticker, start=start.isoformat(), end=end.isoformat(),
                         interval="1d", progress=False, auto_adjust=True)
        if df is None or df.empty:
            return []

        result = []
        close_col = "Close"
        for idx, row in df.iterrows():
            close_val = row[close_col]
            # pandas Series인 경우 scalar로 변환
            if hasattr(close_val, 'iloc'):
                close_val = float(close_val.iloc[0])
            else:
                close_val = float(close_val)
            result.append({
                "date": idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10],
                "close": close_val
            })
        return result
    except Exception as e:
        print(f"    [WARN] {ticker} 데이터 수집 실패: {e}")
        return []


def compute_returns(prices):
    """일간 수익률 리스트 반환."""
    if len(prices) < 2:
        return []
    returns = []
    for i in range(1, len(prices)):
        prev = prices[i - 1]["close"]
        curr = prices[i]["close"]
        if prev and prev != 0:
            returns.append((curr - prev) / prev)
    return returns


def compute_stats(returns):
    """평균(μ), 표준편차(σ) 계산."""
    if len(returns) < 2:
        return 0.0, 0.0
    n = len(returns)
    mu = sum(returns) / n
    variance = sum((r - mu) ** 2 for r in returns) / (n - 1)
    sigma = math.sqrt(variance)
    return mu, sigma


def analyze_assets():
    """
    각 감시 자산의 최근 변동성을 분석하고 2σ 초과 여부를 판단합니다.
    Returns: dict {asset_key: {...분석 결과...}}
    """
    print("  [GEO] 자산 변동성 분석 중...")
    results = {}

    for key, info in WATCH_ASSETS.items():
        ticker = info["ticker"]
        print(f"    - {info['name']} ({ticker}) 데이터 수집...")
        prices = fetch_asset_data(ticker, period_days=40)

        if len(prices) < LOOKBACK_DAYS + 1:
            print(f"      [SKIP] 데이터 부족 ({len(prices)}일)")
            results[key] = {
                "name": info["name"],
                "icon": info["icon"],
                "latest_price": None,
                "latest_return": None,
                "mu": None,
                "sigma": None,
                "z_score": None,
                "alert": False,
                "alert_level": "UNKNOWN",
                "error": "데이터 부족"
            }
            continue

        # 최근 LOOKBACK_DAYS+1개만 사용
        recent_prices = prices[-(LOOKBACK_DAYS + 1):]
        returns = compute_returns(recent_prices)

        # 가장 최근 수익률은 감지 대상
        latest_return = returns[-1] if returns else 0.0
        # 이전 수익률로 μ, σ 계산
        hist_returns = returns[:-1]
        mu, sigma = compute_stats(hist_returns)

        # Z-score
        z_score = (latest_return - mu) / sigma if sigma > 0 else 0.0
        alert = abs(z_score) >= SIGMA_THRESHOLD

        # 경보 레벨
        abs_z = abs(z_score)
        if abs_z >= 4.0:
            level = "EXTREME"
        elif abs_z >= 3.0:
            level = "HIGH"
        elif abs_z >= SIGMA_THRESHOLD:
            level = "MODERATE"
        else:
            level = "NORMAL"

        latest_price = recent_prices[-1]["close"] if recent_prices else None

        print(f"      latest: {latest_price:.2f}, ret: {latest_return*100:.2f}%, "
              f"mu={mu*100:.3f}%, sigma={sigma*100:.3f}%, Z={z_score:.2f} -> {level}{' [ALERT]' if alert else ''}")

        results[key] = {
            "name": info["name"],
            "icon": info["icon"],
            "latest_price": round(latest_price, 4) if latest_price else None,
            "latest_return": round(latest_return * 100, 4),
            "mu": round(mu * 100, 4),
            "sigma": round(sigma * 100, 4),
            "z_score": round(z_score, 3),
            "alert": alert,
            "alert_level": level,
            "price_history": recent_prices[-20:]  # 차트용 최근 20일
        }

    return results


def determine_overall_risk(asset_results):
    """
    전체 리스크 레벨 및 발동된 리스크 유형을 결정합니다.
    """
    alert_count = sum(1 for v in asset_results.values() if v.get("alert"))
    max_level_order = {"NORMAL": 0, "MODERATE": 1, "HIGH": 2, "EXTREME": 3, "UNKNOWN": -1}

    max_level = "NORMAL"
    for v in asset_results.values():
        lvl = v.get("alert_level", "NORMAL")
        if max_level_order.get(lvl, 0) > max_level_order.get(max_level, 0):
            max_level = lvl

    # 전체 경보 레벨 결정
    if alert_count == 0:
        overall = "NORMAL"
    elif alert_count == 1:
        overall = max_level
    elif alert_count == 2:
        overall = "HIGH" if max_level in ("MODERATE", "HIGH") else "EXTREME"
    else:
        overall = "EXTREME"

    # 발동된 리스크 유형 태그 생성
    risk_types = set()
    if asset_results.get("WTI", {}).get("alert"):
        risk_types.add("OIL_SPIKE")
    if asset_results.get("GOLD", {}).get("alert"):
        risk_types.add("GOLD_SPIKE")
    if asset_results.get("ITA", {}).get("alert"):
        risk_types.add("WAR")
    if "OIL_SPIKE" in risk_types and "WAR" in risk_types:
        risk_types.add("CONFLICT")

    return {
        "level": overall,
        "alert_count": alert_count,
        "active": alert_count > 0,
        "risk_types": list(risk_types)
    }


def get_beneficiary_stocks(db, risk_types):
    """
    발동된 리스크 유형에 맞는 수혜 예상 국내 종목을 DB에서 조회합니다.
    """
    print("  [GEO] 수혜 예상 종목 발굴 중...")
    stocks = db.get_market_stocks(limit=None, sort_by='prediction')
    if not stocks:
        return []

    # 빠른 조회를 위해 코드 → 종목 dict 구성
    stock_map = {s[0]: s for s in stocks}

    beneficiary = []

    for sector_name, sector_info in BENEFICIARY_SECTORS.items():
        # 이 섹터가 현재 발동된 리스크 타입과 매칭되는지 확인
        sector_risk_types = sector_info.get("risk_types", [])
        # risk_types가 비어 있으면 모두 표시, 아니면 교집합이 있어야 함
        if risk_types and not any(rt in risk_types for rt in sector_risk_types):
            continue

        sector_stocks = []

        # 1. 섹터 키워드 매칭
        keywords = sector_info["keywords"]
        for s in stocks:
            sector_val = s[3] if len(s) > 3 and s[3] else ""
            name_val = s[1] if len(s) > 1 and s[1] else ""
            combined = (sector_val + " " + name_val).lower()

            if any(kw in combined for kw in keywords):
                # AI 점수 (index 21)
                ai_score = s[21] if len(s) > 21 and s[21] else 0
                prediction = s[8] if len(s) > 8 else None
                sector_stocks.append({
                    "code": s[0],
                    "name": s[1],
                    "market": s[2],
                    "sector": s[3],
                    "price": float(s[4]) if s[4] else 0,
                    "prediction": prediction,
                    "ai_score": int(ai_score)
                })

        # 2. 직접 매핑 보완 (섹터 키워드로 못 잡은 대표 종목)
        existing_codes = {s["code"] for s in sector_stocks}
        for code in DIRECT_MAPPING.get(sector_name, []):
            if code not in existing_codes and code in stock_map:
                s = stock_map[code]
                ai_score = s[21] if len(s) > 21 and s[21] else 0
                prediction = s[8] if len(s) > 8 else None
                sector_stocks.append({
                    "code": code,
                    "name": s[1],
                    "market": s[2],
                    "sector": s[3],
                    "price": float(s[4]) if s[4] else 0,
                    "prediction": prediction,
                    "ai_score": int(ai_score)
                })

        # AI 점수 내림차순 정렬, 상위 5개만
        sector_stocks.sort(key=lambda x: x["ai_score"], reverse=True)
        top_stocks = sector_stocks[:5]

        if top_stocks:
            beneficiary.append({
                "sector": sector_name,
                "icon": sector_info["icon"],
                "reason": sector_info["reason"],
                "stocks": top_stocks
            })

    print(f"    - {sum(len(g['stocks']) for g in beneficiary)}개 수혜 종목 발굴 (섹터: {len(beneficiary)}개)")
    return beneficiary


def build_and_save(asset_results, overall_risk, beneficiary_stocks):
    """
    최종 결과를 JS 파일로 저장합니다.
    """
    geo_data = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "overall_risk": overall_risk,
        "assets": asset_results,
        "beneficiary_sectors": beneficiary_stocks,
        "sigma_threshold": SIGMA_THRESHOLD,
        "lookback_days": LOOKBACK_DAYS,
        "description": (
            "WTI 유가, 금 선물, 미 방산 ETF(ITA)의 최근 변동성이 "
            f"과거 {LOOKBACK_DAYS}일 평균 대비 {SIGMA_THRESHOLD}σ 초과 여부를 감지하는 모델입니다."
        )
    }

    output_dir = os.path.join('D:\\', 'joomoki_PJ', 'data')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'geo_risk_data.js')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"const geoRiskData = {json.dumps(geo_data, ensure_ascii=False, default=str)};")

    print(f"  [GEO] 저장 완료: {output_path}")
    return output_path


def run():
    """지정학적 리스크 모델 실행 진입점."""
    print("\n=== 전쟁/지정학적 리스크 모델 실행 ===")

    if not HAS_YFINANCE:
        print("[ERROR] yfinance 미설치. pip install yfinance")
        return

    # 1. 자산 데이터 분석
    asset_results = analyze_assets()

    # 2. 전체 리스크 레벨 결정
    overall_risk = determine_overall_risk(asset_results)
    level = overall_risk["level"]
    print(f"\n  [GEO] 전체 리스크 레벨: {level} "
          f"(발동 자산: {overall_risk['alert_count']}개, "
          f"리스크 유형: {','.join(overall_risk['risk_types']) or 'None'})")

    if overall_risk["active"]:
        print("  [ALERT] Risk detected! Finding beneficiary stocks...")
    else:
        print("  [OK] Normal range. Showing default sector list.")

    # 3. 수혜 종목 발굴 (리스크 비발동 시에도 기본 목록 표시)
    db = StockDBManager()
    beneficiary_stocks = []
    if db.connect():
        try:
            risk_types = overall_risk["risk_types"] if overall_risk["active"] else []
            if not risk_types:
                # 경보 없을 땐 모든 섹터 기본 표시
                risk_types = list({rt for v in BENEFICIARY_SECTORS.values() for rt in v.get("risk_types", [])})
            beneficiary_stocks = get_beneficiary_stocks(db, risk_types)
        finally:
            db.disconnect()
    else:
        print("  [WARN] DB 연결 실패 - 수혜 종목 발굴 생략")

    # 4. 결과 저장
    build_and_save(asset_results, overall_risk, beneficiary_stocks)

    print("=== 완료 ===\n")


if __name__ == "__main__":
    run()
