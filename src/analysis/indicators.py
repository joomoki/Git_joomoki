import pandas as pd

def calculate_ma(df, window):
    """이동평균선 계산"""
    return df['close_price'].rolling(window=window).mean()

def calculate_rsi(df, window=14):
    """RSI(상대강도지수) 계산 (순수 pandas 구현)"""
    delta = df['close_price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    # fillna(0) or 50? 보통 앞부분은 NaN.
    return rsi

def check_golden_cross(df):
    """
    골든크로스 확인 (5일선이 20일선을 상향 돌파)
    최근 2일 데이터를 기준
    """
    if len(df) < 22: # 최소 20일 + 2일 데이터 필요
        return False
        
    ma5 = calculate_ma(df, 5)
    ma20 = calculate_ma(df, 20)
    
    # 어제와 오늘 비교
    if pd.isna(ma5.iloc[-1]) or pd.isna(ma20.iloc[-1]) or pd.isna(ma5.iloc[-2]) or pd.isna(ma20.iloc[-2]):
        return False

    today_ma5 = ma5.iloc[-1]
    today_ma20 = ma20.iloc[-1]
    prev_ma5 = ma5.iloc[-2]
    prev_ma20 = ma20.iloc[-2]
    
    # 어제는 5일선 < 20일선, 오늘은 5일선 > 20일선
    if prev_ma5 <= prev_ma20 and today_ma5 > today_ma20:
        return True
    return False

def check_dead_cross(df):
    """
    데드크로스 확인 (5일선이 20일선을 하향 돌파)
    """
    if len(df) < 22:
        return False
        
    ma5 = calculate_ma(df, 5)
    ma20 = calculate_ma(df, 20)
    
    if pd.isna(ma5.iloc[-1]) or pd.isna(ma20.iloc[-1]) or pd.isna(ma5.iloc[-2]) or pd.isna(ma20.iloc[-2]):
        return False

    today_ma5 = ma5.iloc[-1]
    today_ma20 = ma20.iloc[-1]
    prev_ma5 = ma5.iloc[-2]
    prev_ma20 = ma20.iloc[-2]
    
    if prev_ma5 >= prev_ma20 and today_ma5 < today_ma20:
        return True
    return False

def calculate_macd(df, fast=12, slow=26, signal=9):
    """MACD 계산 (순수 pandas 구현)"""
    # EMA 계산
    ema_fast = df['close_price'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close_price'].ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # DataFrame으로 반환 (기존 코드 호환성을 위해 컬럼명 맞춤)
    macd_df = pd.DataFrame({
        'MACD_12_26_9': macd_line,
        'MACDs_12_26_9': signal_line,
        'MACDh_12_26_9': macd_line - signal_line # 히스토그램
    })
    return macd_df

def calculate_bbands(df, length=20, std=2):
    """볼린저 밴드 계산 (순수 pandas 구현)"""
    sma = df['close_price'].rolling(window=length).mean()
    rstd = df['close_price'].rolling(window=length).std()
    
    upper_band = sma + (std * rstd)
    lower_band = sma - (std * rstd)
    
    bbands_df = pd.DataFrame({
        'BBL_20_2.0': lower_band,
        'BBM_20_2.0': sma,
        'BBU_20_2.0': upper_band
    })
    return bbands_df

def analyze_stock(df):
    """
    종합 분석 결과 반환
    """
    if df.empty or len(df) < 60:
        return {
            "status": "데이터 부족",
            "signals": [],
            "summary": "분석을 위한 데이터가 충분하지 않습니다.",
            "current_price": 0,
            "ma5": 0, "ma20": 0, "ma60": 0, "rsi": 0,
            "macd": 0, "macd_signal": 0,
            "bb_lower": 0, "bb_upper": 0,
            "score": 0
        }
    
    # 지표 계산
    df['MA5'] = calculate_ma(df, 5)
    df['MA20'] = calculate_ma(df, 20)
    df['MA60'] = calculate_ma(df, 60)
    df['RSI'] = calculate_rsi(df)
    
    # MACD 계산
    macd_df = calculate_macd(df)
    if macd_df is not None:
        df = pd.concat([df, macd_df], axis=1)
        
    # 볼린저 밴드 계산
    bbands_df = calculate_bbands(df)
    if bbands_df is not None:
        df = pd.concat([df, bbands_df], axis=1)
    
    current_price = df['close_price'].iloc[-1]
    ma5 = df['MA5'].iloc[-1]
    ma20 = df['MA20'].iloc[-1]
    ma60 = df['MA60'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    volume = df['volume'].iloc[-1]
    avg_volume = df['volume'].iloc[-21:-1].mean() # 최근 20일 평균 거래량
    
    signals = []
    
    # 1. 골든/데드 크로스
    if check_golden_cross(df):
        signals.append({"type": "POSITIVE", "msg": "📈 골든크로스 발생! (단기 상승 신호)"})
    elif check_dead_cross(df):
        signals.append({"type": "NEGATIVE", "msg": "📉 데드크로스 발생! (단기 하락 주의)"})
        
    # 2. 정배열/역배열
    if not pd.isna(ma5) and not pd.isna(ma20) and not pd.isna(ma60):
        if ma5 > ma20 > ma60:
            signals.append({"type": "POSITIVE", "msg": "🚀 정배열 상승 추세 (강력한 매수 구간)"})
        elif ma5 < ma20 < ma60:
            signals.append({"type": "NEGATIVE", "msg": "💧 역배열 하락 추세 (매수 주의)"})
        
    # 3. RSI
    if not pd.isna(rsi):
        if rsi >= 70:
            signals.append({"type": "WARNING", "msg": "🔥 과매수 구간 (RSI > 70) - 차익 실현 고려"})
        elif rsi <= 30:
            signals.append({"type": "OPPORTUNITY", "msg": "💎 과매도 구간 (RSI < 30) - 저점 매수 기회"})

    # 4. MACD (골든크로스: MACD > Signal)
    if 'MACD_12_26_9' in df.columns:
        macd = df['MACD_12_26_9'].iloc[-1]
        macd_signal = df['MACDs_12_26_9'].iloc[-1]
        prev_macd = df['MACD_12_26_9'].iloc[-2]
        prev_signal = df['MACDs_12_26_9'].iloc[-2]
        
        if not pd.isna(macd) and not pd.isna(macd_signal):
            if prev_macd <= prev_signal and macd > macd_signal:
                 signals.append({"type": "POSITIVE", "msg": "🌊 MACD 상향 돌파 (추세 전환 신호)"})
    
    # 5. 볼린저 밴드 (하단 터치)
    if 'BBL_20_2.0' in df.columns:
        bbl = df['BBL_20_2.0'].iloc[-1]
        if not pd.isna(bbl):
            if current_price <= bbl * 1.02: # 하단 밴드 근접 (2% 이내)
                 signals.append({"type": "OPPORTUNITY", "msg": "🛡️ 볼린저 밴드 하단 근접 (반등 가능성)"})

    # 6. 거래량 급증
    if not pd.isna(avg_volume) and avg_volume > 0 and volume > avg_volume * 1.5:
         signals.append({"type": "POSITIVE", "msg": "📢 거래량 급증 (전일 대비 활발)"})
        
    # 종합 의견
    score = 0
    for s in signals:
        if s['type'] in ['POSITIVE', 'OPPORTUNITY']: score += 1
        if s['type'] in ['NEGATIVE', 'WARNING']: score -= 1
        
    if score >= 3: summary = "강력 매수 권장" # 기준 상향
    elif score >= 1: summary = "매수 관점"
    elif score == 0: summary = "관망 (중립)"
    elif score == -1: summary = "매도 관점"
    else: summary = "적극 매도 권장"
    
    today_macd = 0
    today_macd_signal = 0
    today_bbl = 0
    today_bbu = 0

    if 'MACD_12_26_9' in df.columns:
        val = df['MACD_12_26_9'].iloc[-1]
        today_macd = val if not pd.isna(val) else 0
        val_sig = df['MACDs_12_26_9'].iloc[-1]
        today_macd_signal = val_sig if not pd.isna(val_sig) else 0
        
    if 'BBL_20_2.0' in df.columns:
        val_bbl = df['BBL_20_2.0'].iloc[-1]
        today_bbl = val_bbl if not pd.isna(val_bbl) else 0
        val_bbu = df['BBU_20_2.0'].iloc[-1]
        today_bbu = val_bbu if not pd.isna(val_bbu) else 0

    return {
        "status": "OK",
        "current_price": int(current_price),
        "ma5": int(ma5) if not pd.isna(ma5) else 0,
        "ma20": int(ma20) if not pd.isna(ma20) else 0,
        "ma60": int(ma60) if not pd.isna(ma60) else 0,
        "rsi": round(rsi, 2) if not pd.isna(rsi) else 0,
        "macd": round(today_macd, 2),
        "macd_signal": round(today_macd_signal, 2),
        "bb_lower": int(today_bbl),
        "bb_upper": int(today_bbu),
        "signals": signals,
        "summary": summary,
        "score": score
    }
