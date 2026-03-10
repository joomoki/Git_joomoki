
import sys
import os
import json
sys.path.append(os.getcwd())
from src.stock_db_manager import StockDBManager
from config.db_config import SCHEMA_NAME

def get_sort_key(x):
    score = x['analysis'].get('score', 0)
    market_cap = x['financials'].get('market_cap', 0)
    
    # 등락률 계산
    change_rate = 0.0
    if x.get('chart_data') and len(x['chart_data']) >= 2:
        last = x['chart_data'][-1].get('close', 0)
        prev = x['chart_data'][-2].get('close', 0)
        if prev > 0:
            change_rate = (last - prev) / prev
            
            market = x.get('market', '')
            if market in ['KOSPI', 'KOSDAQ', 'KONEX']:
                if abs(change_rate) > 0.3:
                    change_rate = 0.0

    return (score, market_cap, change_rate)

def main():
    db = StockDBManager()
    if not db.connect():
        print("DB Connection Failed")
        return

    try:
        print("Fetching Korea Stocks...")
        # Replicating export_to_web.py call
        korea_stocks = db.get_market_stocks(limit=None, sort_by='prediction')
        print(f"Total fetched: {len(korea_stocks)}")

        # Check raw results for duplicates of Pandora TV
        raw_dups = [s for s in korea_stocks if '판도라티비' in str(s)]
        print(f"Raw Duplicates count: {len(raw_dups)}")
        for d in raw_dups:
            print(f"Raw item: {d[0]} {d[1]} (Index 0/1)") # Adjust based on structure

        formatted_korea = []
        
        for s in korea_stocks:
            # Replicating loop from export_to_web.py
            # 22: price_history
            chart_data = s[22] if (len(s) > 22 and s[22] and isinstance(s[22], list)) else []
            
            # AI Score: DB 저장 값 사용 (s[21])
            final_score = s[21] if (len(s) > 21 and s[21] is not None) else 0

            # Description: s[25] (added in query? Let's check index)
            # In stock_db_manager.py get_market_stocks:
            # 0:code, 1:name, 2:market, 3:sector, 4:price, 5:volume, 6:date, 7:summary, 8:pred
            # 9:per, 10:pbr, 11:cap, 12:eps, 13:bps, 14:sales, 15:op_profit, 16:debt, 17:frgn, 18:pgm
            # 19:conf, 20:signals, 21:score, 22:history, 23:frgn_trend, 24:inst_trend, 25:desc
            
            description = s[25] if (len(s) > 25) else None

            stock_obj = {
                "code": s[0],
                "name": s[1],
                "market": s[2],
                "price": float(s[4]) if s[4] else 0,
                "chart_data": chart_data,
                "analysis": {
                    "score": final_score,
                },
                "financials": {
                    "market_cap": float(s[11]) if s[11] else 0,
                }
            }
            formatted_korea.append(stock_obj)

        # Check duplicates in formatted list
        fmt_dups = [s for s in formatted_korea if '판도라티비' in s['name']]
        print(f"Formatted Duplicates count: {len(fmt_dups)}")

        # apply sort
        formatted_korea.sort(key=get_sort_key, reverse=True)
        
        # Check Sort Order
        print("\n--- Top 20 Sorted Items ---")
        for i, item in enumerate(formatted_korea[:20]):
            score = item['analysis']['score']
            name = item['name']
            print(f"{i+1}. {name}: {score}")

        # Check if 80 is after 68
        # Scan list to see sequence of scores
        print("\n--- Score Sequence Check ---")
        last_score = 1000
        for i, item in enumerate(formatted_korea):
            score = item['analysis']['score']
            if score > last_score:
                print(f"SORT ERROR at index {i}: {score} > {last_score} (Item: {item['name']})")
                # Print context
                prev = formatted_korea[i-1]
                print(f"  Prev: {prev['name']} ({prev['analysis']['score']})")
                break
            last_score = score
        else:
            print("Sort order is correct (Descending)")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()
