
import json
import re

def verify_js_file(filepath):
    print(f"Verifying {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract JSON from "stockData.stocks = stockData.stocks.concat([...]);"
        # or simplified JS structure used in chunks.
        # Pattern match for the JSON array
        match = re.search(r'concat\((.*)\);', content, re.DOTALL)
        if not match:
            # Maybe it's not using concat?
            # Check file content structure in step 1019: `if(typeof ... concat(...)`
            # Pattern: `concat([ ... ])`
            match = re.search(r'concat\(\s*(\[.*\])\s*\)', content, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            print(f"Loaded {len(data)} items.")
            
            # 1. Check Duplicates
            names = [item['name'] for item in data]
            pandora_count = names.count('판도라티비')
            print(f"'판도라티비' count: {pandora_count}")
            
            if pandora_count > 1:
                dups = [item for item in data if item['name'] == '판도라티비']
                for i, d in enumerate(dups):
                    print(f"  Instance {i+1}: Score={d['analysis'].get('score')}, Code={d['code']}")

            # 2. Check Sort Order
            print("\nChecking Sort Order (Score DESC):")
            last_score = 1000
            error_count = 0
            for i, item in enumerate(data):
                score = item['analysis'].get('score', 0)
                name = item['name']
                if score > last_score:
                    if error_count < 5:
                        print(f"  SORT ERROR at index {i}: {name} (Score {score}) > Prev (Score {last_score})")
                    error_count += 1
                last_score = score
            
            if error_count == 0:
                print("Sort order seems correct.")
            else:
                print(f"Total Sort Errors: {error_count}")

            # print top 10
            print("\nTop 10 in file:")
            for item in data[:10]:
                 print(f"  {item['name']}: {item['analysis'].get('score')}")

        else:
            print("Could not find JSON array in file.")
            print("File content preview:", content[:200])

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_js_file('d:/joomoki_PJ/stock_portal_joomoki/data/stock_data_kr_1.js')
