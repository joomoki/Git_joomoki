
import psycopg2
import sys
import os

# 상위 디렉토리 경로 추가 (config 모듈 import 위함)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import DB_CONFIG, SCHEMA_NAME

def add_ai_score_column():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. 국내 주식 분석 테이블 컬럼 추가
        print("Checking stock_analysis table...")
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{SCHEMA_NAME}' 
            AND table_name = 'stock_analysis' 
            AND column_name = 'ai_score';
        """)
        if not cur.fetchone():
            print("Adding ai_score column to stock_analysis...")
            cur.execute(f"ALTER TABLE {SCHEMA_NAME}.stock_analysis ADD COLUMN ai_score INTEGER DEFAULT 0;")
        else:
            print("ai_score column already exists in stock_analysis.")
            
        # 2. 미국 주식 분석 테이블 컬럼 추가
        print("Checking us_stock_analysis table...")
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{SCHEMA_NAME}' 
            AND table_name = 'us_stock_analysis' 
            AND column_name = 'ai_score';
        """)
        if not cur.fetchone():
            print("Adding ai_score column to us_stock_analysis...")
            cur.execute(f"ALTER TABLE {SCHEMA_NAME}.us_stock_analysis ADD COLUMN ai_score INTEGER DEFAULT 0;")
        else:
            print("ai_score column already exists in us_stock_analysis.")

        # 3. 미국 주식 분석 테이블 updated_at 컬럼 추가
        print("Checking us_stock_analysis table for updated_at...")
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{SCHEMA_NAME}' 
            AND table_name = 'us_stock_analysis' 
            AND column_name = 'updated_at';
        """)
        if not cur.fetchone():
            print("Adding updated_at column to us_stock_analysis...")
            cur.execute(f"ALTER TABLE {SCHEMA_NAME}.us_stock_analysis ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
        else:
            print("updated_at column already exists in us_stock_analysis.")

        # 4. 국내 주식 분석 테이블 updated_at 컬럼 추가
        print("Checking stock_analysis table for updated_at...")
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{SCHEMA_NAME}' 
            AND table_name = 'stock_analysis' 
            AND column_name = 'updated_at';
        """)
        if not cur.fetchone():
            print("Adding updated_at column to stock_analysis...")
            cur.execute(f"ALTER TABLE {SCHEMA_NAME}.stock_analysis ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
        else:
            print("updated_at column already exists in stock_analysis.")

        conn.commit()
        print("Schema update completed successfully.")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error updating schema: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_ai_score_column()
