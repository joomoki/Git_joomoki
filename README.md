# 뉴스-주식 분석 시스템

뉴스 크롤링과 주식 데이터를 연계하여 투자 분석을 수행하는 시스템입니다.

## 📁 프로젝트 구조

```
joomoki_PJ/
├── src/                    # 소스 코드
│   ├── crawler_with_db.py      # 뉴스 크롤링 + DB 저장
│   ├── stock_crawler.py        # 주식 데이터 크롤링
│   ├── news_stock_analyzer.py  # 뉴스-주식 분석
│   └── run_analysis.py         # 통합 실행 스크립트
├── config/                 # 설정 파일
│   └── db_config.py           # 데이터베이스 설정
├── scripts/               # 유틸리티 스크립트
│   └── test_db_connection.py  # DB 연결 테스트
├── sql/                   # SQL 스크립트
│   ├── create_schema.sql      # 기본 스키마 생성
│   └── create_stock_schema.sql # 주식 스키마 생성
├── docs/                  # 문서
│   └── setup_instructions.md  # 설정 가이드
└── WCD/                   # 크롤링 데이터 저장
    └── daum_news_article.json
```

## 🚀 설치 및 설정

### 1. 필요한 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 2. PostgreSQL 데이터베이스 설정
```bash
# 데이터베이스 생성
psql -U postgres
CREATE DATABASE news_crawler;

# 스키마 및 테이블 생성
psql -U postgres -d news_crawler -f sql/create_schema.sql
psql -U postgres -d news_crawler -f sql/create_stock_schema.sql
```

### 3. 데이터베이스 연결 설정
`config/db_config.py`에서 연결 정보 수정:
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'news_crawler',
    'user': 'postgres',
    'password': 'your_password'  # 실제 비밀번호로 변경
}
```

## 📊 데이터베이스 스키마

### 뉴스 관련 테이블
- `news_articles`: 뉴스 기사 정보
- `related_links`: 관련 기사 링크

### 주식 관련 테이블
- `stock_companies`: 주식 종목 정보
- `stock_prices`: 주식 가격 데이터
- `news_stock_relations`: 뉴스-주식 연결
- `stock_keywords`: 주식 관련 키워드
- `stock_analysis`: 주식 분석 결과

## 🔧 사용법

### 전체 분석 실행
```bash
python src/run_analysis.py full
```

### 개별 모듈 실행
```bash
# 뉴스 크롤링만
python src/run_analysis.py news

# 주식 데이터 크롤링만
python src/run_analysis.py stock

# 분석만
python src/run_analysis.py analysis
```

### 개별 스크립트 실행
```bash
# 뉴스 크롤링
python src/crawler_with_db.py

# 주식 데이터 크롤링
python src/stock_crawler.py

# 뉴스-주식 분석
python src/news_stock_analyzer.py
```

## 📈 주요 기능

### 1. 뉴스 크롤링
- 다음뉴스 기사 크롤링
- 제목, 본문, 작성자, 날짜 등 추출
- PostgreSQL에 자동 저장

### 2. 주식 데이터 수집
- 주식 종목 정보 수집
- 가격 데이터 수집 (시가, 고가, 저가, 종가, 거래량)
- 시가총액, 업종 정보 포함

### 3. 뉴스-주식 분석
- 뉴스에서 주식 관련 키워드 추출
- 감정 분석 (긍정/부정/중립)
- 뉴스 영향도 점수 계산
- 가격 예측 및 투자 신호 생성

### 4. 분석 결과
- 종목별 뉴스 영향도 점수
- 감정 트렌드 분석
- 가격 예측 (상승/하락/보합)
- 신뢰도 점수

## 🎯 분석 알고리즘

### 키워드 매핑
- 뉴스 텍스트에서 주식 종목명 추출
- 회사명, 브랜드명, 약칭 등 다양한 형태 인식

### 감정 분석
- 긍정 키워드: 상승, 호재, 성장, 확대, 수주 등
- 부정 키워드: 하락, 악재, 감소, 손실, 위험 등
- 감정 점수: -1.0 (매우 부정) ~ 1.0 (매우 긍정)

### 영향도 계산
```
뉴스 영향도 = 평균 감정 점수 × 평균 관련도 × 뉴스 건수 × 10
```

### 가격 예측
- 감정 점수 > 0.3: 상승 예측
- 감정 점수 < -0.3: 하락 예측
- 그 외: 보합 예측

## 📊 모니터링

### 데이터베이스 연결 테스트
```bash
python scripts/test_db_connection.py
```

### 저장된 데이터 확인
```sql
-- 뉴스 기사 수
SELECT COUNT(*) FROM joomoki_news.news_articles;

-- 주식 종목 수
SELECT COUNT(*) FROM joomoki_news.stock_companies;

-- 분석 결과
SELECT * FROM joomoki_news.stock_analysis 
ORDER BY news_impact_score DESC LIMIT 10;
```

## 🔄 자동화

### 스케줄링 (Windows Task Scheduler)
1. 작업 스케줄러 열기
2. 기본 작업 만들기
3. 트리거: 매일 특정 시간
4. 동작: `python D:\joomoki_PJ\src\run_analysis.py full`

### 배치 파일 생성
```batch
@echo off
cd /d D:\joomoki_PJ
python src\run_analysis.py full
pause
```

## ⚠️ 주의사항

1. **데이터 정확성**: 샘플 데이터를 사용하므로 실제 투자 결정에 사용하지 마세요
2. **API 제한**: 실제 금융 데이터 API 사용 시 요청 제한 확인
3. **법적 고려사항**: 웹 크롤링 시 robots.txt 및 이용약관 준수
4. **데이터 보안**: 데이터베이스 비밀번호 등 민감한 정보 보호

## 🛠️ 확장 가능성

- 더 많은 뉴스 사이트 지원
- 실시간 데이터 수집
- 머신러닝 모델 적용
- 웹 대시보드 구축
- 모바일 앱 개발
- 알림 시스템 구축

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. PostgreSQL 서비스 실행 상태
2. 데이터베이스 연결 설정
3. 필요한 라이브러리 설치 여부
4. 네트워크 연결 상태