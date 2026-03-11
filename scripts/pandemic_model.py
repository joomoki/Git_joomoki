#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
질병/팬데믹 모델 (섹터 로테이션 및 비대면 수혜 중심)
- XLV(의료 ETF), IBB(바이오 ETF), ARKK 변동성 감지
- 언택트/바이오/클라우드/물류 섹터 수혜 종목 발굴
- Money Flow Index(MFI) 기반 자금 유입 분석
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
# 감시 자산 (질병/바이오 리스크 지표)
# ─────────────────────────────────────
WATCH_ASSETS = {
    "XLV":  {"ticker": "XLV",   "name": "미 헬스케어 ETF(XLV)",   "icon": "🏥"},
    "IBB":  {"ticker": "IBB",   "name": "미 바이오테크 ETF(IBB)",  "icon": "🧬"},
    "ARKK": {"ticker": "ARKK",  "name": "ARK 혁신 ETF(ARKK)",     "icon": "🚀"},
    "XAR":  {"ticker": "XAR",   "name": "항공우주/방산 ETF (피해지표)", "icon": "✈️"},
}

# 피해 섹터 (자금이 빠져나가는 쪽)
DAMAGE_TICKERS = {"XAR"}  # 이 ETF가 하락 시 팬데믹 효과 강화

LOOKBACK_DAYS = 20
SIGMA_THRESHOLD = 1.5   # 팬데믹은 좀 민감하게 (1.5σ)

# ─────────────────────────────────────
# 수혜 섹터 정의
# ─────────────────────────────────────
BENEFICIARY_SECTORS = {
    "바이오·헬스케어": {
        "keywords": ["바이오", "제약", "의료", "진단", "백신", "헬스", "의약품", "치료"],
        "icon": "🧬",
        "reason": "질병 확산 시 진단·치료·백신 수요 급증",
        "mfi_bias": "inflow"
    },
    "언택트·플랫폼": {
        "keywords": ["소프트웨어", "플랫폼", "게임", "인터넷", "온라인", "이커머스", "미디어"],
        "icon": "💻",
        "reason": "비대면 전환 시 언택트 서비스 수요 폭발",
        "mfi_bias": "inflow"
    },
    "물류·배달": {
        "keywords": ["물류", "택배", "배달", "배송", "유통", "쿠팡", "CJ대한통운"],
        "icon": "📦",
        "reason": "이동 제한 시 배달·물류 급증",
        "mfi_bias": "inflow"
    },
    "클라우드·보안": {
        "keywords": ["클라우드", "보안", "네트워크", "IDC", "데이터", "통신"],
        "icon": "☁️",
        "reason": "재택근무 확산 시 클라우드·보안 인프라 수요 급등",
        "mfi_bias": "inflow"
    }
}

# 직접 코드 매핑 (키워드 미탐지 보완)
DIRECT_MAPPING = {
    "바이오·헬스케어": ["068270", "000661", "005930", "091990", "302440", "207940", "196170", "293490"],
    "언택트·플랫폼": ["035720", "036570", "251270", "263750", "293490", "041510"],
    "물류·배달": ["000120", "011200", "004490", "086280", "000480"],
    "클라우드·보안": ["030200", "032640", "017670", "00553K", "018260"]
}

# 피해 섹터 키워드 (자금이탈 쪽 - 검토용)
DAMAGE_SECTORS_KEYWORDS = ["항공", "여행", "호텔", "면세", "카지노", "레저", "공연", "영화관"]


def fetch_asset_data(ticker, period_days=35):
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
        for idx, row in df.iterrows():
            close_val = row["Close"]
            vol_val = row["Volume"] if "Volume" in row else 0
            high_val = row["High"] if "High" in row else close_val
            low_val = row["Low"] if "Low" in row else close_val
            for v in [close_val, vol_val, high_val, low_val]:
                if hasattr(v, 'iloc'):
                    v = float(v.iloc[0])
            close_val = float(close_val.iloc[0]) if hasattr(close_val, 'iloc') else float(close_val)
            vol_val = float(vol_val.iloc[0]) if hasattr(vol_val, 'iloc') else float(vol_val)
            high_val = float(high_val.iloc[0]) if hasattr(high_val, 'iloc') else float(high_val)
            low_val = float(low_val.iloc[0]) if hasattr(low_val, 'iloc') else float(low_val)
            result.append({
                "date": idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10],
                "close": close_val,
                "volume": vol_val,
                "high": high_val,
                "low": low_val,
            })
        return result
    except Exception as e:
        print(f"    [WARN] {ticker} 수집 실패: {e}")
        return []


def compute_returns(prices):
    if len(prices) < 2:
        return []
    return [((prices[i]["close"] - prices[i-1]["close"]) / prices[i-1]["close"])
            for i in range(1, len(prices))
            if prices[i-1]["close"] != 0]


def compute_stats(returns):
    if len(returns) < 2:
        return 0.0, 0.0
    n = len(returns)
    mu = sum(returns) / n
    variance = sum((r - mu) ** 2 for r in returns) / (n - 1)
    return mu, math.sqrt(variance)


def compute_mfi(prices, period=14):
    """
    Money Flow Index 근사 계산 (전형가격 기반).
    MFI > 50 = 순매수 압력 (inflow)
    MFI < 50 = 순매도 압력 (outflow)
    """
    if len(prices) < period + 1:
        return 50.0

    tp_list = [((p["high"] + p["low"] + p["close"]) / 3) for p in prices]
    raw_mf = [(tp_list[i] * prices[i].get("volume", 0)) for i in range(len(prices))]

    pos_mf = sum(raw_mf[i] for i in range(1, len(prices)) if tp_list[i] >= tp_list[i-1])
    neg_mf = sum(raw_mf[i] for i in range(1, len(prices)) if tp_list[i] < tp_list[i-1])

    if neg_mf == 0:
        return 100.0
    mfr = pos_mf / neg_mf
    return round(100 - (100 / (1 + mfr)), 2)


def analyze_assets():
    """헬스케어/바이오 ETF 변동성 + MFI 분석."""
    print("  [PANDEMIC] 자산 변동성 분석 중...")
    results = {}

    for key, info in WATCH_ASSETS.items():
        ticker = info["ticker"]
        print(f"    - {info['name']} ({ticker}) 수집...")
        prices = fetch_asset_data(ticker, period_days=40)

        if len(prices) < LOOKBACK_DAYS + 1:
            results[key] = {"name": info["name"], "icon": info["icon"],
                            "alert": False, "alert_level": "UNKNOWN", "error": "데이터 부족",
                            "mfi": 50.0, "is_damage": key in DAMAGE_TICKERS}
            continue

        recent = prices[-(LOOKBACK_DAYS + 1):]
        returns = compute_returns(recent)
        latest_return = returns[-1] if returns else 0.0
        mu, sigma = compute_stats(returns[:-1])
        z_score = (latest_return - mu) / sigma if sigma > 0 else 0.0
        mfi = compute_mfi(recent[-15:])

        abs_z = abs(z_score)
        is_damage = key in DAMAGE_TICKERS

        # 피해 섹터가 하락하면 팬데믹 시그널 강화
        if is_damage:
            alert = z_score <= -SIGMA_THRESHOLD  # 피해 섹터 하락
        else:
            alert = z_score >= SIGMA_THRESHOLD   # 수혜 섹터 상승

        if abs_z >= 3.5:
            level = "EXTREME"
        elif abs_z >= 2.5:
            level = "HIGH"
        elif abs_z >= SIGMA_THRESHOLD:
            level = "MODERATE"
        else:
            level = "NORMAL"

        latest_price = recent[-1]["close"] if recent else None

        print(f"      latest: {latest_price:.2f}, ret: {latest_return*100:.2f}%, "
              f"Z={z_score:.2f} -> {level}{' [ALERT]' if alert else ''}, MFI={mfi}")

        results[key] = {
            "name": info["name"],
            "icon": info["icon"],
            "latest_price": round(latest_price, 4) if latest_price else None,
            "latest_return": round(latest_return * 100, 4),
            "mu": round(mu * 100, 4),
            "sigma": round(sigma * 100, 4),
            "z_score": round(z_score, 3),
            "mfi": mfi,
            "alert": alert,
            "alert_level": level,
            "is_damage": is_damage,
            "price_history": recent[-20:]
        }

    return results


def determine_pandemic_risk(asset_results):
    """팬데믹 리스크 레벨 결정."""
    benefit_alerts = sum(1 for k, v in asset_results.items()
                         if v.get("alert") and not v.get("is_damage"))
    damage_alerts = sum(1 for k, v in asset_results.items()
                        if v.get("alert") and v.get("is_damage"))
    total_signals = benefit_alerts + damage_alerts

    if total_signals == 0:
        level = "NORMAL"
    elif total_signals == 1:
        level = "MODERATE"
    elif total_signals == 2:
        level = "HIGH"
    else:
        level = "EXTREME"

    # 자금이탈 신호 분석 (피해섹터 MFI < 40 이면 이탈 가속)
    damage_mfi = [v.get("mfi", 50) for k, v in asset_results.items() if v.get("is_damage")]
    benefit_mfi = [v.get("mfi", 50) for k, v in asset_results.items() if not v.get("is_damage")]
    money_flow_signal = "ROTATION" if (
        damage_mfi and benefit_mfi and
        (sum(damage_mfi) / len(damage_mfi)) < 45 and
        (sum(benefit_mfi) / len(benefit_mfi)) > 55
    ) else "NEUTRAL"

    return {
        "level": level,
        "active": total_signals > 0,
        "benefit_alert_count": benefit_alerts,
        "damage_alert_count": damage_alerts,
        "money_flow_signal": money_flow_signal,
        "description": (
            f"수혜 ETF {benefit_alerts}개 상승 경보, 피해 ETF {damage_alerts}개 하락 경보 감지."
            if total_signals > 0 else "현재 정상 범위 내 변동성."
        )
    }


def get_beneficiary_stocks(db, pandemic_risk):
    """DB에서 언택트/바이오 수혜 예상 국내 종목 발굴."""
    print("  [PANDEMIC] 수혜 예상 종목 발굴 중...")
    stocks = db.get_market_stocks(limit=None, sort_by='prediction')
    if not stocks:
        return []

    stock_map = {s[0]: s for s in stocks}
    beneficiary = []

    for sector_name, sector_info in BENEFICIARY_SECTORS.items():
        sector_stocks = []
        keywords = sector_info["keywords"]

        for s in stocks:
            sector_val = (s[3] or "") if len(s) > 3 else ""
            name_val = (s[1] or "") if len(s) > 1 else ""
            combined = (sector_val + " " + name_val).lower()
            if any(kw in combined for kw in keywords):
                ai_score = s[21] if len(s) > 21 and s[21] else 0
                prediction = s[8] if len(s) > 8 else None
                sector_stocks.append({
                    "code": s[0], "name": s[1], "market": s[2],
                    "sector": s[3], "price": float(s[4]) if s[4] else 0,
                    "prediction": prediction, "ai_score": int(ai_score)
                })

        # 직접 매핑 보완
        existing = {s["code"] for s in sector_stocks}
        for code in DIRECT_MAPPING.get(sector_name, []):
            if code not in existing and code in stock_map:
                s = stock_map[code]
                ai_score = s[21] if len(s) > 21 and s[21] else 0
                sector_stocks.append({
                    "code": code, "name": s[1], "market": s[2],
                    "sector": s[3], "price": float(s[4]) if s[4] else 0,
                    "prediction": s[8] if len(s) > 8 else None, "ai_score": int(ai_score)
                })

        sector_stocks.sort(key=lambda x: x["ai_score"], reverse=True)
        top = sector_stocks[:5]
        if top:
            beneficiary.append({
                "sector": sector_name,
                "icon": sector_info["icon"],
                "reason": sector_info["reason"],
                "mfi_bias": sector_info["mfi_bias"],
                "stocks": top
            })

    # 피해 섹터 종목도 별도로 나열 (투자 주의용)
    damage_stocks = []
    for s in stocks:
        sector_val = (s[3] or "") if len(s) > 3 else ""
        name_val = (s[1] or "") if len(s) > 1 else ""
        combined = (sector_val + " " + name_val).lower()
        if any(kw in combined for kw in DAMAGE_SECTORS_KEYWORDS):
            damage_stocks.append({"code": s[0], "name": s[1], "sector": s[3]})

    print(f"    - {sum(len(g['stocks']) for g in beneficiary)}개 수혜 종목, {len(damage_stocks)}개 피해 종목 식별")
    return beneficiary, damage_stocks[:10]


def build_and_save(asset_results, pandemic_risk, beneficiary_sectors, damage_stocks):
    """결과를 JS 파일로 저장."""
    data = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "pandemic_risk": pandemic_risk,
        "assets": asset_results,
        "beneficiary_sectors": beneficiary_sectors,
        "damage_stocks": damage_stocks,
        "sigma_threshold": SIGMA_THRESHOLD,
        "lookback_days": LOOKBACK_DAYS,
        "model_description": (
            "XLV(의료 ETF), IBB(바이오 ETF), ARKK 변동성을 "
            f"{LOOKBACK_DAYS}일 히스토리 대비 {SIGMA_THRESHOLD}σ 초과 여부로 감지하는 팬데믹 모델입니다."
        )
    }
    output_dir = os.path.join("D:\\", "joomoki_PJ", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "pandemic_data.js")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"const pandemicData = {json.dumps(data, ensure_ascii=False, default=str)};")
    print(f"  [PANDEMIC] 저장 완료: {output_path}")
    return output_path


def run():
    """팬데믹 모델 실행 진입점."""
    print("\n=== 질병/팬데믹 모델 실행 ===")
    if not HAS_YFINANCE:
        print("[ERROR] yfinance 미설치. pip install yfinance")
        return

    asset_results = analyze_assets()
    pandemic_risk = determine_pandemic_risk(asset_results)
    print(f"\n  [PANDEMIC] 리스크 레벨: {pandemic_risk['level']} "
          f"| 자금 흐름: {pandemic_risk['money_flow_signal']}")

    db = StockDBManager()
    beneficiary_sectors = []
    damage_stocks = []
    if db.connect():
        try:
            result = get_beneficiary_stocks(db, pandemic_risk)
            if isinstance(result, tuple):
                beneficiary_sectors, damage_stocks = result
            else:
                beneficiary_sectors = result
        finally:
            db.disconnect()
    else:
        print("  [WARN] DB 연결 실패")

    build_and_save(asset_results, pandemic_risk, beneficiary_sectors, damage_stocks)
    print("=== 완료 ===\n")


if __name__ == "__main__":
    run()
