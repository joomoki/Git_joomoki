#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
국내 주식 최종 데이터 삭제 후 최신화 스크립트
1. DB 현황 확인
2. daily_price 테이블의 최신 날짜 이후 데이터 수집
3. 웹 export 실행
"""

import sys
import os
import time
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME

try:
    import FinanceDataReader as fdr
    HAS_FDR = True
except ImportError:
    HAS_FDR = False
    print("[WARN] FinanceDataReader가 없습니다.")


def check_db_status(db):
    """DB 현황 출력"""
    print("\n=== DB 현황 확인 ===")
    with db.conn.cursor() as cur:
        # stock_prices 최신 날짜
        cur.execute(f"SELECT MAX(trade_date), COUNT(*) FROM {SCHEMA_NAME}.stock_prices")
        r = cur.fetchone()
        print(f"  stock_prices: 최신={r[0]}, 건수={r[1]}")

        # daily_price 최신 날짜
        cur.execute(f"SELECT MAX(trade_date), COUNT(*) FROM {SCHEMA_NAME}.daily_price")
        r = cur.fetchone()
        print(f"  daily_price:  최신={r[0]}, 건수={r[1]}")

        # 국내 종목 수
        cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.stock_companies")
        r = cur.fetchone()
        print(f"  국내 종목 수: {r[0]}개")

        # 전체에서 최신 날짜 (두 테이블 합산)
        cur.execute(f"""
            SELECT MAX(trade_date) FROM (
                SELECT trade_date FROM {SCHEMA_NAME}.stock_prices
                UNION ALL
                SELECT trade_date FROM {SCHEMA_NAME}.daily_price
            ) t
        """)
        r = cur.fetchone()
        print(f"  전체 최신 날짜: {r[0]}")
    print()


def delete_latest_kr_data(db):
    """
    국내 주식의 최신 날짜 데이터만 삭제 (daily_price 기준)
    """
    print("=== 국내 주식 최신 날짜 데이터 삭제 ===")
    
    with db.conn.cursor() as cur:
        # daily_price 테이블에서 최신 날짜 확인
        cur.execute(f"SELECT MAX(trade_date) FROM {SCHEMA_NAME}.daily_price")
        max_date = cur.fetchone()[0]
        
        if not max_date:
            print("  daily_price에 데이터가 없습니다.")
            return None
        
        print(f"  daily_price 최신 날짜: {max_date}")
        
        # 해당 날짜 데이터 건수 확인
        cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.daily_price WHERE trade_date = %s", (max_date,))
        cnt = cur.fetchone()[0]
        print(f"  삭제 대상: {max_date} 날짜 {cnt}건")
        
        # 삭제
        cur.execute(f"DELETE FROM {SCHEMA_NAME}.daily_price WHERE trade_date = %s", (max_date,))
        deleted = cur.rowcount
        
        # stock_prices에서도 동일 날짜 삭제
        cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.stock_prices WHERE trade_date = %s", (max_date,))
        sp_cnt = cur.fetchone()[0]
        if sp_cnt > 0:
            cur.execute(f"DELETE FROM {SCHEMA_NAME}.stock_prices WHERE trade_date = %s", (max_date,))
            sp_deleted = cur.rowcount
            print(f"  stock_prices에서 {sp_deleted}건 삭제")
        
        # stock_analysis에서도 해당 날짜 삭제
        cur.execute(f"DELETE FROM {SCHEMA_NAME}.stock_analysis WHERE analysis_date = %s", (max_date,))
        sa_deleted = cur.rowcount
        if sa_deleted > 0:
            print(f"  stock_analysis에서 {sa_deleted}건 삭제")
        
    db.conn.commit()
    print(f"  [완료] 총 {deleted}건 삭제 (날짜: {max_date})")
    return max_date


def update_kr_prices(db):
    """
    FinanceDataReader로 국내 전종목 최신 데이터 수집
    """
    if not HAS_FDR:
        print("[ERROR] FinanceDataReader가 설치되지 않았습니다.")
        return

    print("\n=== 국내 주식 최신 데이터 수집 ===")
    
    # 종목 목록 가져오기
    stocks = db.get_all_stocks()
    total = len(stocks)
    print(f"  수집 대상: {total}개 종목")
    
    today = datetime.now()
    end_date = today.strftime('%Y-%m-%d')
    default_start_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
    
    success = 0
    skip = 0
    error = 0
    
    for i, (stock_code, market_type, company_name) in enumerate(stocks):
        try:
            # 마지막 수집일 확인 (두 테이블 모두 확인)
            with db.conn.cursor() as cur:
                cur.execute(f"""
                    SELECT MAX(trade_date) FROM (
                        SELECT trade_date FROM {SCHEMA_NAME}.stock_prices WHERE stock_code = %s
                        UNION ALL
                        SELECT trade_date FROM {SCHEMA_NAME}.daily_price WHERE stock_code = %s
                    ) t
                """, (stock_code, stock_code))
                last_date = cur.fetchone()[0]
            
            if last_date:
                start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                start_date = default_start_date

            # 이미 최신이면 스킵
            if start_date > end_date:
                skip += 1
                continue

            if i % 50 == 0:
                print(f"  [{i+1}/{total}] 진행 중... (성공: {success}, 스킵: {skip}, 실패: {error})")

            # 데이터 다운로드
            df = fdr.DataReader(stock_code, start_date, end_date)
            
            if df is None or df.empty:
                skip += 1
                continue

            # 데이터 변환
            price_data = []
            for date_idx, row in df.iterrows():
                trade_date = date_idx.strftime('%Y-%m-%d')
                row = row.fillna(0)
                price_tuple = (
                    trade_date,
                    float(row.get('Open', 0)),
                    float(row.get('High', 0)),
                    float(row.get('Low', 0)),
                    float(row.get('Close', 0)),
                    int(row.get('Volume', 0)),
                    0  # market_cap
                )
                price_data.append(price_tuple)

            if price_data and db.insert_price_list(stock_code, price_data):
                success += 1
            else:
                error += 1
                
        except Exception as e:
            print(f"  [실패] {stock_code} {company_name}: {e}")
            error += 1

    print(f"\n[완료] 성공: {success}, 스킵: {skip}, 실패: {error}")


def run_export():
    """웹 export 실행"""
    print("\n=== 웹 데이터 내보내기 ===")
    try:
        from src.export_to_web import export_data
        export_data()
    except Exception as e:
        print(f"[ERROR] export 실패: {e}")
        import traceback
        traceback.print_exc()


def run_geo_risk_model():
    """지정학적 리스크 모델 실행"""
    print("\n=== 지정학적 리스크 모델 ===")
    try:
        from scripts.geo_risk_model import run as geo_run
        geo_run()
    except Exception as e:
        print(f"[WARN] 지정학 리스크 모델 실패 (선택 기능): {e}")
        import traceback
        traceback.print_exc()


def run_pandemic_model():
    """질병/팬데믹 모델 실행"""
    print("\n=== 질병/팬데믹 모델 ===")
    try:
        from scripts.pandemic_model import run as pandemic_run
        pandemic_run()
    except Exception as e:
        print(f"[WARN] 팬데믹 모델 실패 (선택 기능): {e}")
        import traceback
        traceback.print_exc()


def run_semi_dip_model():
    """반도체 SOX 급락 줍줍 모델 실행"""
    print("\n=== 반도체 SOX 줍줍 모델 ===")
    try:
        from scripts.semi_dip_model import run as semi_run
        semi_run()
    except Exception as e:
        print(f"[WARN] 반도체 줍줍 모델 실패 (선택 기능): {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    db = StockDBManager()
    if not db.connect():
        print("[ERROR] DB 연결 실패")
        sys.exit(1)

    try:
        # 1. 현황 확인
        check_db_status(db)
        
        # 2. 최신 날짜 데이터 삭제
        deleted_date = delete_latest_kr_data(db)
        
        # 3. 삭제 후 현황 다시 확인
        check_db_status(db)
        
        # 4. 최신 데이터 수집
        update_kr_prices(db)
        
    finally:
        db.disconnect()

    # 5. 웹 export
    run_export()

    # 6. 지정학적 리스크 모델
    run_geo_risk_model()

    # 7. 질병/팬데믹 모델
    run_pandemic_model()

    # 8. 반도체 SOX 급락 줍줍 모델
    run_semi_dip_model()
    
    print("\n=== 전체 작업 완료 ===")
