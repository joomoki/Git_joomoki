# PostgreSQL 데이터베이스 설정 가이드

## 1. PostgreSQL 설치 확인

PostgreSQL이 설치되어 있는지 확인하세요:
```bash
psql --version
```

## 2. 데이터베이스 생성

### 방법 1: psql 명령어 사용
```bash
# PostgreSQL에 접속 (postgres 사용자로)
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE news_crawler;

# 데이터베이스에 접속
\c news_crawler

# 테이블 생성 (setup_database.sql 파일 실행)
\i setup_database.sql

# 종료
\q
```

### 방법 2: pgAdmin 사용
1. pgAdmin을 실행
2. 서버 연결
3. 데이터베이스 우클릭 → Create → Database
4. 이름: `news_crawler` 입력
5. 생성 완료

## 3. Python 라이브러리 설치

```bash
pip install psycopg2-binary sqlalchemy
```

## 4. 데이터베이스 연결 정보 설정

`database_manager.py` 파일에서 다음 정보를 수정하세요:

```python
db_manager = DatabaseManager(
    host='localhost',        # 기본값
    port=5432,              # 기본값
    database='news_crawler', # 생성한 데이터베이스명
    user='postgres',         # PostgreSQL 사용자명
    password='your_password' # 실제 비밀번호로 변경
)
```

## 5. 테이블 생성 및 테스트

```bash
python database_manager.py
```

## 6. 크롤링 데이터 저장

```bash
python crawler_with_db.py
```

## 주요 테이블 구조

### news_articles 테이블
- `id`: 기본키 (자동증가)
- `url`: 기사 URL (유니크)
- `title`: 기사 제목
- `content`: 기사 본문
- `author`: 작성자
- `publish_date`: 발행일
- `category`: 카테고리
- `summary`: 요약
- `crawled_at`: 크롤링 시간
- `created_at`: 생성 시간
- `updated_at`: 수정 시간

### related_links 테이블
- `id`: 기본키
- `article_id`: 기사 ID (외래키)
- `title`: 관련 기사 제목
- `url`: 관련 기사 URL
- `created_at`: 생성 시간

## 유용한 SQL 쿼리

```sql
-- 모든 기사 조회
SELECT * FROM news_articles ORDER BY crawled_at DESC;

-- 특정 키워드 검색
SELECT * FROM news_articles WHERE title ILIKE '%키워드%';

-- 카테고리별 기사 수
SELECT category, COUNT(*) FROM news_articles GROUP BY category;

-- 최근 7일간 크롤링된 기사
SELECT * FROM news_articles WHERE crawled_at >= NOW() - INTERVAL '7 days';
```
