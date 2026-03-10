-- joomoki_news 스키마 테이블 구조 및 한글명 확인

-- 1. 테이블 목록 및 설명 조회
SELECT 
    schemaname as "스키마명",
    tablename as "테이블명",
    obj_description(oid) as "테이블 설명"
FROM pg_tables 
WHERE schemaname = 'joomoki_news'
ORDER BY tablename;

-- 2. news_articles 테이블 상세 구조
SELECT 
    column_name as "컬럼명",
    data_type as "데이터타입",
    character_maximum_length as "최대길이",
    is_nullable as "NULL허용",
    column_default as "기본값",
    col_description(pgc.oid, ordinal_position) as "컬럼설명"
FROM information_schema.columns isc
JOIN pg_class pgc ON pgc.relname = isc.table_name
WHERE table_schema = 'joomoki_news'
  AND table_name = 'news_articles'
ORDER BY ordinal_position;

-- 3. related_links 테이블 상세 구조
SELECT 
    column_name as "컬럼명",
    data_type as "데이터타입",
    character_maximum_length as "최대길이",
    is_nullable as "NULL허용",
    column_default as "기본값",
    col_description(pgc.oid, ordinal_position) as "컬럼설명"
FROM information_schema.columns isc
JOIN pg_class pgc ON pgc.relname = isc.table_name
WHERE table_schema = 'joomoki_news'
  AND table_name = 'related_links'
ORDER BY ordinal_position;

-- 4. 인덱스 정보 조회
SELECT 
    schemaname as "스키마명",
    tablename as "테이블명",
    indexname as "인덱스명",
    indexdef as "인덱스 정의",
    obj_description(indexrelid) as "인덱스 설명"
FROM pg_indexes 
WHERE schemaname = 'joomoki_news'
ORDER BY tablename, indexname;

-- 5. 외래키 관계 조회
SELECT
    tc.table_schema as "스키마명",
    tc.table_name as "테이블명",
    tc.column_name as "컬럼명",
    ccu.table_schema as "참조스키마",
    ccu.table_name as "참조테이블",
    ccu.column_name as "참조컬럼"
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'joomoki_news'
ORDER BY tc.table_name, tc.column_name;
