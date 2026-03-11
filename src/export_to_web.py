#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 포털용 데이터 내보내기 스크립트 (국내 + 미국)
"""

import sys
import os
import json
import datetime
import concurrent.futures
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_db_manager import StockDBManager
from src.exchange_rate import get_usd_krw_rate
from config.db_config import SCHEMA_NAME

def calculate_and_save_korea_scores(db, target_date=None):
    """
    국내 주식 AI 점수를 일괄 계산하여 DB에 저장 (최대 10개)
    """
    print("  - Calculating and updating Korea AI Scores...")
    stocks = db.get_market_stocks(limit=None, target_date=target_date)
    
    # 계산할 기준 일시 확정 (가장 최근 거래일 등)
    if not target_date and stocks:
        # stocks 튜플: s[6]이 trade_date (get_market_stocks 쿼리 참조)
        # 모든 종목을 순회하며 가장 최신 날짜를 찾음
        valid_dates = [s[6] for s in stocks if len(s) > 6 and s[6]]
        if valid_dates:
            target_date = max(valid_dates)
    
    if target_date and db.conn:
        try:
            with db.conn.cursor() as cur:
                # 1. 해당 날짜의 기존 AI 점수 초기화
                cur.execute(f"UPDATE {SCHEMA_NAME}.stock_analysis SET ai_score = 0 WHERE analysis_date = %s", (target_date,))
                cur.execute(f"UPDATE {SCHEMA_NAME}.daily_price SET ai_score = 0 WHERE trade_date = %s", (target_date,))
            db.conn.commit()
            print(f"    - Cleared existing Korea AI scores for {target_date}")
        except Exception as e:
            print(f"    - Failed to clear existing Korea AI scores: {e}")
            db.conn.rollback()

    calculated_stocks = []
    for s in stocks:
        try:
            stock_code = s[0]
            prediction = s[8]
            
            chart_data = s[22] if (len(s) > 22 and s[22] and isinstance(s[22], list)) else []
            confidence = s[19] if len(s) > 19 and s[19] is not None else 0.0
            signals = s[20] if len(s) > 20 and s[20] else []
            signal_count = len(signals) if isinstance(signals, list) else 0
            
            # 1. 기본 점수
            if prediction == 'UP': base_score = 60
            elif prediction == 'DOWN': base_score = 30
            else: base_score = 45

            add_score = 0
            if confidence > 0: add_score += (confidence * 15)
            add_score += min(signal_count * 3, 10)
            
            if s[17] and s[17] > 0: add_score += 3
            if s[18] and s[18] > 0: add_score += 3

            if len(chart_data) >= 5:
                last_close = chart_data[-1].get('close', 0)
                prev_close = chart_data[-2].get('close', 0)
                if prev_close > 0:
                    chg_rate = ((last_close - prev_close) / prev_close) * 100
                    add_score += max(min(chg_rate, 10), -5)

                vols = [d.get('volume', 0) for d in chart_data[-5:]]
                if len(vols) >= 5:
                    avg_vol = sum(vols[:-1]) / 4 if sum(vols[:-1]) > 0 else 1
                    curr_vol = vols[-1]
                    if curr_vol > avg_vol * 1.5: add_score += 2
                    if curr_vol > avg_vol * 3.0: add_score += 3

                if len(chart_data) >= 3:
                    c1 = chart_data[-1].get('close', 0)
                    c2 = chart_data[-2].get('close', 0)
                    c3 = chart_data[-3].get('close', 0)
                    if c1 > c2 > c3:
                        add_score += 3

            try:
                per = float(s[9]) if s[9] else 0
                pbr = float(s[10]) if s[10] else 0
                if 0 < per < 5: add_score += 5
                elif 5 <= per < 10: add_score += 3
                elif 10 <= per < 20: add_score += 1
                if 0 < pbr < 0.5: add_score += 5
                elif 0.5 <= pbr < 1.0: add_score += 3
                elif 1.0 <= pbr < 2.0: add_score += 1
            except:
                pass

            final_score = int(min(max(base_score + add_score, 10), 99))
            market_cap = float(s[11]) if s[11] else 0

            analysis_date = s[6]
            if not analysis_date and target_date:
                analysis_date = target_date
                
            if analysis_date:
                calculated_stocks.append({
                    'code': stock_code,
                    'score': final_score,
                    'market_cap': market_cap,
                    'date': analysis_date
                })
                
        except Exception as e:
            continue
            
    # 정렬: 1. 점수 내림차순, 2. 시가총액 내림차순
    calculated_stocks.sort(key=lambda x: (x['score'], x['market_cap']), reverse=True)
    
    # 상위 10개만 저장
    top_10_stocks = calculated_stocks[:10]
    count = 0
    for stock in top_10_stocks:
        db.update_ai_score(stock['code'], stock['score'], stock['date'], is_us=False)
        count += 1
            
    print(f"    - Updated {count} Korea stocks AI scores (Top 10 limit applied).")

def calculate_and_save_us_scores(db, target_date=None):
    """
    미국 주식 AI 점수 일괄 계산 및 저장 (최대 10개)
    """
    print("  - Calculating and updating US AI Scores...")
    stocks = db.get_us_market_stocks(limit=None, target_date=target_date)
    
    if not target_date and stocks:
        valid_dates = [s[7] for s in stocks if len(s) > 7 and s[7]]
        if valid_dates:
            target_date = max(valid_dates)
            
    if target_date and db.conn:
        try:
            with db.conn.cursor() as cur:
                # 1. 해당 날짜의 기존 US AI 점수 초기화
                cur.execute(f"UPDATE {SCHEMA_NAME}.us_stock_analysis SET ai_score = 0 WHERE analysis_date = %s", (target_date,))
                cur.execute(f"UPDATE {SCHEMA_NAME}.us_stock_prices SET ai_score = 0 WHERE trade_date = %s", (target_date,))
            db.conn.commit()
            print(f"    - Cleared existing US AI scores for {target_date}")
        except Exception as e:
            print(f"    - Failed to clear existing US AI scores: {e}")
            db.conn.rollback()
    
    calculated_stocks = []
    for s in stocks:
        try:
            stock_code = s[0]
            prediction = s[9]
            sentiment = s[10] if s[10] is not None else 0
            confidence = s[11] if s[11] is not None else 0.5
            trade_date = s[7]
            market_cap = float(s[13]) if s[13] else 0
            
            if prediction == 'UP':
                base_score = 70 + (confidence * 20) + (max(0, sentiment) * 10)
                base_score = min(base_score, 99)
            elif prediction == 'DOWN':
                base_score = 30 - (confidence * 20)
                base_score = max(5, base_score)
            else:
                base_score = 50 + (sentiment * 10)
                
            final_score = int(min(max(base_score, 0), 100))
            
            if trade_date:
                calculated_stocks.append({
                    'code': stock_code,
                    'score': final_score,
                    'market_cap': market_cap,
                    'date': trade_date
                })
                
        except Exception as e:
            continue
            
    calculated_stocks.sort(key=lambda x: (x['score'], x['market_cap']), reverse=True)
    
    top_10_stocks = calculated_stocks[:10]
    count = 0
    for stock in top_10_stocks:
        db.update_ai_score(stock['code'], stock['score'], stock['date'], is_us=True)
        count += 1
            
    print(f"    - Updated {count} US stocks AI scores (Top 10 limit applied).")

def process_us_stock(s):
    """
    US stock processing worker function.
    Reads s (tuple), fetches news, translates, and returns stock object.
    """
    # Create thread-local DB connection
    db = StockDBManager()
    if not db.connect():
        return None

    try:
        # 번역기 초기화
        translator = None
        use_translator = False
        
        # 번역 기능 비활성화 (속도 문제 해결 위해)
        # try:
        #     from googletrans import Translator
        #     translator = Translator()
        #     use_translator = True
        # except ImportError:
        #     try:
        #         from deep_translator import GoogleTranslator
        #         translator = GoogleTranslator(source='auto', target='ko')
        #         use_translator = True
        #     except ImportError:
        #         use_translator = False
        # except Exception:
        #     use_translator = False

        # 쿼리 결과 s unpacking (StockDBManager.get_us_market_stocks 수정 반영)
        # 0:code, 1:name, 2:korean_name, 3:market, 4:sector, 
        # 5:price, 6:vol, 7:date, 8:summary, 9:pred, 
        # 10:sentiment_score, 11:confidence, 12:ai_score,
        # 13:cap, 14:history, 15:per, 16:eps, 17:pbr, 18:roe, 19:description
        
        company_name = s[1]
        korean_name = s[2]
        
        # 한국어 이름이 없거나, 영어 이름과 같다면 번역 시도
        if not korean_name or korean_name == company_name:
            if use_translator:
                try:
                    if hasattr(translator, 'translate'): 
                        if "googletrans" in str(type(translator)):
                            translated = translator.translate(company_name, dest='ko').text
                        else:
                            translated = translator.translate(company_name)
                        if translated and translated != company_name:
                            korean_name = translated
                except Exception:
                    pass
        
        display_name = company_name
        if korean_name and korean_name != company_name:
            display_name = korean_name

        # 뉴스 데이터 조회
        news_items = db.get_us_stock_news(s[0], limit=5)
        formatted_news = []
        for n in news_items:
            # 0:date, 1:title, 2:link, 3:source, 4:label
            title = n[1]
            if use_translator:
                try:
                    if hasattr(translator, 'translate'): 
                        if "googletrans" in str(type(translator)):
                            translated = translator.translate(title, dest='ko').text
                        else:
                            translated = translator.translate(title)
                        title = translated
                except Exception:
                    pass
            
            news_date_str = ""
            if n[0]:
                if isinstance(n[0], str):
                    news_date_str = n[0][:10]
                elif hasattr(n[0], 'strftime'):
                    news_date_str = n[0].strftime("%Y-%m-%d")

            formatted_news.append({
                "date": news_date_str,
                "title": title,
                "link": n[2],
                "sentiment": n[4]
            })
            
        chart_data = s[14] if s[14] else [] # 14: price_history

        # AI Score: DB에 저장된 값 사용
        final_score = s[12] if s[12] is not None else 0

        stock_obj = {
            "code": s[0],
            "name": company_name, # 영어 이름 그대로 유지
            "korean_name": korean_name, # 번역 로직 거친 최신 값
            "market": s[3],
            "price": float(s[5]) if s[5] else 0,
            "volume": s[6],
            "volume": s[6],
            "chart_data": chart_data,
            "description": s[19] if len(s) > 19 else None, 
            "major_index": s[20] if len(s) > 20 else None, # Added (index changed)
            "analysis": {
                "summary": s[8],
                "prediction": s[9],
                "score": final_score,
                "per": float(s[15]) if s[15] else None, 
                "eps": float(s[16]) if s[16] else None,
                "news": formatted_news
            },
            "financials": {
                "market_cap": float(s[13]) if s[13] else 0
            },
            "investor": {} 
        }
        return stock_obj
    except Exception as e:
        print(f"[WARN] Error processing {s[0]}: {e}")
        return None
    finally:
        db.disconnect()

def export_data():
    print("[INFO] Exporting Web Data...")
    db = StockDBManager()
    
    if not db.connect():
        print("[ERROR] DB Connection Failed")
        return

    # 0. DB VIEW/함수 설정 (최초 실행 시 CREATE OR REPLACE)
    db.setup_views_and_functions()

    # 0-1. AI 점수 계산 (DB 함수 호출 - Python 계산 이전)
    print("  - Calculating Korea AI Scores in DB...")
    n = db.calculate_korea_ai_scores_in_db()
    print(f"    - {n} rows updated via DB function.")
    # calculate_and_save_us_scores(db)  # 해외주식 Export 중단

    # 1. 국내 주식 데이터 조회
    print("  - Fetching Korea Stocks...")
    # 쿼리 결과 인덱스 변경됨: ..., 19:confidence, 20:signals, 21:ai_score, 22:price_history, 23:..., 24:..., 25:description
    korea_stocks = db.get_market_stocks(limit=None, sort_by='prediction')
    
    formatted_korea = []
    top_picks_korea = []
    
    for s in korea_stocks:
        # 인덱스 참조: 0:code, 1:name, 2:market, 3:sector, 4:close, 5:vol, 6:trade_date
        # 7:summary, 8:prediction, 9:per, 10:pbr, 11:market_cap, 12:eps, 13:bps
        # 14:sales, 15:op_profit, 16:debt_ratio, 17:frgn_net_buy, 18:pgm_net_buy
        # 19:confidence, 20:signals, 21:ai_score, 22:price_history, 23:frgn_trend
        # 24:inst_trend, 25:description, 26:change_rate (DB VIEW)
        chart_data = s[22] if (len(s) > 22 and s[22] and isinstance(s[22], list)) else []
        final_score = s[21] if (len(s) > 21 and s[21] is not None) else 0
        description = s[25] if (len(s) > 25) else None
        change_rate_db = float(s[26]) if (len(s) > 26 and s[26] is not None) else 0.0

        stock_obj = {
            "code": s[0],
            "name": s[1],
            "market": s[2],
            "price": float(s[4]) if s[4] else 0,
            "volume": s[5],
            "chart_data": chart_data,
            "description": description,
            "change_rate": change_rate_db,  # DB VIEW에서 직접 가져온 등락률
            "analysis": {
                "summary": s[7],
                "prediction": s[8],
                "score": final_score,
                "per": float(s[9]) if s[9] else None,
                "pbr": float(s[10]) if s[10] else None
            },
            "financials": {
                "market_cap": float(s[11]) if s[11] else 0,
                "eps": float(s[12]) if s[12] else None,
                "bps": float(s[13]) if s[13] else None,
                "sales": float(s[14]) if s[14] else None,
                "op_profit": float(s[15]) if s[15] else None,
                "debt_ratio": float(s[16]) if s[16] else None,
            },
            "investor": {
                 "frgn_net_buy": s[17],
                 "pgm_net_buy": s[18],
                 "frgn_trend": s[23] if len(s) > 23 and s[23] else [],
                 "inst_trend": s[24] if len(s) > 24 and s[24] else []
            }
        }
        formatted_korea.append(stock_obj)
        if s[8] == 'UP':
            top_picks_korea.append(stock_obj)


    # 2. 미국 주식 - 해외 주식 Export 중단 (DB 데이터는 유지)
    formatted_us = []
    top_picks_us = []
    print("  - [SKIP] US Stocks export disabled.")

    # 정렬: AI 점수 높은 순 (내림차순)
    top_picks_korea.sort(key=lambda x: x['analysis'].get('score', 0), reverse=True)
    top_picks_us.sort(key=lambda x: x['analysis'].get('score', 0), reverse=True)

    # 전체 리스트 정렬: AI 점수 > 시가총액 > 등락률 (DB에서 가져온 change_rate 사용)
    def get_sort_key(x):
        score = x['analysis'].get('score', 0)
        market_cap = x['financials'].get('market_cap', 0)
        # DB VIEW(v_latest_price_with_change)에서 change_rate를 stock_obj에 넣어뒀으면 바로 사용
        change_rate = x.get('change_rate', 0.0) or 0.0
        return (score, market_cap, change_rate)

    print("  - Sorting entire lists by AI Score > Market Cap > Change Rate (DB-sourced)...")
    formatted_korea.sort(key=get_sort_key, reverse=True)
    formatted_us.sort(key=get_sort_key, reverse=True)

    # 3. 데이터 분할 및 파일 생성 (Chunking)
    print("  - Chunking and saving data...")
    
    # 3-1. Base Data (Metadata & Top Picks)
    # Calculate max dates
    korea_date = "-"
    if formatted_korea:
        # Assuming format YYYYMMDD in DB, but let's check. 
        # In get_market_stocks: s[6] is dates (analysis_date?). 
        # Actually in loop: s[6] is volume? No.
        # Let's check loop unpacking again.
        # korea_stocks loop: s[0] code... s[6] (analysis_date? No, wait)
        # DB Query (get_market_stocks): 
        # SELECT code, name, ..., price, volume, date, ...
        # Standard: 0:code, 1:name, 2:market, 3:sector, 4:price, 5:volume, 6:date
        # Let's verify with DB manager code or just take a safe bet from the data loop.
        # Actually in the loop `formatted_korea` doesn't have date explicitly saved in top level.
        # But we can get it from `s[6]` inside the loop if we saved it?
        # Re-reading loop:
        # for s in korea_stocks:
        #    ... stock_obj = { ... }
        #    formatted_korea.append(stock_obj)
        # We need to extract max date from `korea_stocks` (s[6]) directly.
        pass

    # Re-scan for max dates
    k_dates = [s[6] for s in korea_stocks if len(s) > 6 and s[6]]
    korea_date = max(k_dates) if k_dates else "-"
    
    # Format Korea date (YYYYMMDD -> YYYY-MM-DD)
    if isinstance(korea_date, str) and len(korea_date) == 8:
        korea_date = f"{korea_date[:4]}-{korea_date[4:6]}-{korea_date[6:]}"
    elif hasattr(korea_date, 'strftime'):
        korea_date = korea_date.strftime("%Y-%m-%d")

    # US Dates - 해외 주식 비활성화, 고정값 사용
    us_date = "-"

    base_data = {
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "market_dates": {
            "korea": korea_date,
            "us": us_date
        },
        "exchange_rate": get_usd_krw_rate(),
        "stats": {
            "korea_total": len(formatted_korea),
            "us_total": len(formatted_us)
        },
        "top_picks": top_picks_korea,
        "us_top_picks": top_picks_us,
        "stocks": [],     # To be populated by chunks
        "us_stocks": []   # To be populated by chunks
    }
    
    data_dir = os.path.join('D:\\', 'DataStock', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    base_file_path = os.path.join(data_dir, 'stock_data_base.js')
    with open(base_file_path, 'w', encoding='utf-8') as f:
        f.write(f"const stockData = {json.dumps(base_data, ensure_ascii=False)};")
    print(f"    - Saved base data: {base_file_path}")
    
    generated_files = ['data/stock_data_base.js']
    
    # Helper to save chunks
    def save_chunks(data_list, prefix, variable_name):
        chunk_size = 500  # Number of items per chunk (adjust as needed to keep under 5MB)
        # Assuming ~2KB per stock item, 500 items is ~1MB. Safe margin.
        
        chunks = [data_list[i:i + chunk_size] for i in range(0, len(data_list), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            filename = f"stock_data_{prefix}_{i+1}.js"
            filepath = os.path.join(data_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json_str = json.dumps(chunk, ensure_ascii=False)
                # Append to existing array
                f.write(f"if(typeof stockData !== 'undefined') {{ stockData.{variable_name} = stockData.{variable_name}.concat({json_str}); }}")
            
            print(f"    - Saved chunk: {filename} ({len(chunk)} items)")
            generated_files.append(f"data/{filename}")

    # 3-2. Save Korea Stocks Chunks
    save_chunks(formatted_korea, 'kr', 'stocks')
    
    # 3-3. US Stocks Chunks - 해외 중단으로 저장 안 함
    # save_chunks(formatted_us, 'us', 'us_stocks')
    
    # 4. Update index.html
    print("  - Updating index.html...")
    index_html_path = os.path.join(os.path.dirname(data_dir), 'index.html')
    
    with open(index_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    # Generate new script tags
    script_tags = '\n    '.join([f'<script src="{f}"></script>' for f in generated_files])
    
    start_marker = '<!-- STOCK_DATA_SCRIPTS_START -->'
    end_marker = '<!-- STOCK_DATA_SCRIPTS_END -->'
    
    start_idx = html_content.find(start_marker)
    end_idx = html_content.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        new_html = (
            html_content[:start_idx + len(start_marker)] + 
            '\n    ' + script_tags + '\n    ' + 
            html_content[end_idx:]
        )
        with open(index_html_path, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print(f"[SUCCESS] Updated index.html with {len(generated_files)} script tags.")
    else:
        print("[WARN] Markers not found in index.html. Could not auto-update.")

    print(f"[SUCCESS] Export Completed.")
    print(f"   - Korea: {len(formatted_korea)}")
    print(f"   - US: {len(formatted_us)}")

    # 5. 추천 이력 저장 (대시보드와 동일한 Top 6 저장)
    # 5. 추천 이력 저장 (대시보드와 동일한 Top 6 저장)
    print("  - Processing Recommendation History...")
    # KR Top 6
    final_top_kr = top_picks_korea[:6]
    # US Top 6 - 해외 중단
    final_top_us = []   # 해외 주식 제외
    
    # 대표 날짜 선정 (Korea 기준)
    target_rec_date = korea_date if korea_date and len(korea_date) == 10 else datetime.datetime.now().strftime("%Y-%m-%d")
    
    save_history(db, final_top_kr, final_top_us, target_date=target_rec_date)
    
    # 6. 분석 데이터 내보내기
    export_history_data(db, data_dir)
    db.disconnect()

def save_history(db, top_korea, top_us, target_date=None):
    """
    오늘의 AI 추천 종목(Top 6)을 그대로 이력 테이블에 저장
    대시보드와 일치시키기 위해 별도의 필터링 없이 전달받은 리스트를 저장함.
    저장 전 해당 날짜의 기존 이력을 삭제하여 중복 및 불일치 방지.
    """
    count = 0
    
    # 날짜 확정
    rec_date = target_date if target_date else datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 해당 날짜의 기존 데이터 삭제 (중복/불일치 해결의 핵심)
    print(f"    - Clearing existing history for {rec_date}...")
    db.delete_recommendation_history(rec_date)
    
    # Combined list for processing
    # Add is_us flag if not present (though export_data usually processes them cleanly)
    
    # Korea
    for s in top_korea:
        s['is_us'] = False
        
    # US
    for s in top_us:
        s['is_us'] = True
        
    candidates = top_korea + top_us
    
    for s in candidates:
        code = s['code']
        price = s['price']
        score = s['analysis'].get('score', 0)
        is_us = s.get('is_us', False)
        
        # 날짜 추출 (개별 종목 날짜 무시하고 target_date로 통일하여 저장)
        # Why? 대시보드는 "현재" 기준이고, 히스토리는 "그 날의 대시보드 상태"를 저장해야 하므로.
        final_rec_date = rec_date
        
        # 날짜 포맷 확인 (YYYY-MM-DD)
        if hasattr(final_rec_date, 'strftime'):
            final_rec_date = final_rec_date.strftime("%Y-%m-%d")

            
        if db.save_recommendation_history(code, rec_date, price, score, is_us=is_us):
            count += 1

    print(f"    - Saved {count} recommendation history items (KR {len(top_korea)} + US {len(top_us)}).")

def export_history_data(db, data_dir):
    """
    수익률 분석 데이터를 JS 파일로 저장
    """
    history = db.get_recommendation_history_with_performance()
    
    # 데이터 가공
    # [{date: '...', code: '...', name: '...', base: ..., current: ..., return: ..., score: ...}, ...]
    formatted_history = []
    
    for row in history:
        # row: date, code, name, market_type, base, current, return, score, is_us
        rec_date = row[0]
        if hasattr(rec_date, 'strftime'):
            rec_date = rec_date.strftime("%Y-%m-%d")
            
        stock_obj = {
            "date": rec_date,
            "code": row[1],
            "name": row[2],
            "market": row[3],
            "base_price": float(row[4]) if row[4] else 0,
            "current_price": float(row[5]) if row[5] else 0,
            "return_rate": float(row[6]) if row[6] is not None else 0,
            "score": row[7],
            "is_us": row[8],
            "description": db.get_stock_description(row[1], is_us=row[8]),
            "performance_history": []
        }
        
        # 수익률 추적 데이터 (추천일 이후 시세) -> performance_history
        if rec_date:
            daily_prices = db.get_daily_prices_after(row[1], rec_date, is_us=row[8])
            base_price = float(row[4]) if row[4] else 0
            
            perf_list = []
            for d_date, d_close in daily_prices:
                d_date_str = str(d_date)
                d_close = float(d_close) if d_close else 0
                
                # 수익률 계산
                ret = 0.0
                if base_price > 0:
                    ret = ((d_close - base_price) / base_price) * 100
                
                perf_list.append({
                    "date": d_date_str,
                    "close": d_close,
                    "return": round(ret, 2)
                })
            
            stock_obj["performance_history"] = perf_list
            
            # [NEW] 상세 차트용 전체 시세 데이터 (OHLCV) - 최근 120일
            chart_data = []
            try:
                rows_chart = db.get_daily_price_ohlcv(row[1], limit=120, is_us=row[8])
                
                for r in rows_chart:
                    chart_data.append({
                        "date": str(r[0]),
                        "open": float(r[1]) if r[1] else 0,
                        "high": float(r[2]) if r[2] else 0,
                        "low": float(r[3]) if r[3] else 0,
                        "close": float(r[4]) if r[4] else 0,
                        "volume": int(r[5]) if r[5] else 0
                    })
                        
            except Exception as e:
                print(f"Error fetching chart data for {row[1]}: {e}")
                
            stock_obj["price_history"] = chart_data
            
        formatted_history.append(stock_obj)
        
    file_path = os.path.join(data_dir, 'stock_data_history.js')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"const stockHistoryData = {json.dumps(formatted_history, ensure_ascii=False)};")
    
    print(f"    - Saved history data: {file_path} ({len(formatted_history)} items)")

if __name__ == "__main__":
    export_data()
