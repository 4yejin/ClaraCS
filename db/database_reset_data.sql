-- ========================================
-- ClaraCS 업무 데이터 초기화 스크립트
-- ========================================
-- 작성일: 2025-10-18
-- 설명: 업로드, 분류, 리포트 데이터만 삭제 (코드성 데이터는 유지)
-- 
-- 유지되는 테이블 (코드성 데이터):
--   - tb_uploaded_file_extension_code (파일 확장자 코드)
--   - tb_column_mapping_code (컬럼 매핑 코드)
--   - tb_category (카테고리 마스터)
--   - tb_user (사용자)
--
-- 삭제되는 테이블 (업무 데이터):
--   - 업로드 관련, 티켓, 분류 결과, 리포트 등
-- ========================================

USE clara_cs;

-- 외래키 체크 임시 비활성화
SET FOREIGN_KEY_CHECKS = 0;

-- ========================================
-- 1. 리포트 관련 데이터 삭제 (외래키 종속성 순서대로)
-- ========================================

-- 1-1. 리포트 스냅샷 테이블들 (report_id에 종속)
TRUNCATE TABLE tb_analysis_summary_snapshot;
TRUNCATE TABLE tb_analysis_insight_snapshot;
TRUNCATE TABLE tb_analysis_solution_snapshot;
TRUNCATE TABLE tb_analysis_channel_snapshot;

-- 1-2. 리포트 메인 테이블
TRUNCATE TABLE tb_analysis_report;

-- ========================================
-- 2. 분류 결과 데이터 삭제
-- ========================================

-- 2-1. 카테고리별 분류 결과 (class_result_id에 종속)
TRUNCATE TABLE tb_classification_category_result;

-- 2-2. 분류 결과 메인 테이블
TRUNCATE TABLE tb_classification_result;

-- ========================================
-- 3. 티켓 데이터 삭제
-- ========================================
TRUNCATE TABLE tb_ticket;

-- ========================================
-- 4. 컬럼 매핑 데이터 삭제 (파일별 매핑)
-- ========================================
TRUNCATE TABLE tb_column_mapping;

-- ========================================
-- 5. 업로드 파일 데이터 삭제
-- ========================================
TRUNCATE TABLE tb_uploaded_file;

-- 외래키 체크 다시 활성화
SET FOREIGN_KEY_CHECKS = 1;

-- ========================================
-- 확인 쿼리
-- ========================================

-- 남아있는 데이터 확인 (코드성 데이터만 있어야 함)
SELECT '파일 확장자 코드' as 테이블, COUNT(*) as 개수 FROM tb_uploaded_file_extension_code
UNION ALL
SELECT '컬럼 매핑 코드', COUNT(*) FROM tb_column_mapping_code
UNION ALL
SELECT '카테고리', COUNT(*) FROM tb_category
UNION ALL
SELECT '사용자', COUNT(*) FROM tb_user
UNION ALL
SELECT '--- 업무 데이터 (0이어야 함) ---', 0
UNION ALL
SELECT '업로드 파일', COUNT(*) FROM tb_uploaded_file
UNION ALL
SELECT '컬럼 매핑', COUNT(*) FROM tb_column_mapping
UNION ALL
SELECT '티켓', COUNT(*) FROM tb_ticket
UNION ALL
SELECT '분류 결과', COUNT(*) FROM tb_classification_result
UNION ALL
SELECT '카테고리별 분류 결과', COUNT(*) FROM tb_classification_category_result
UNION ALL
SELECT '분석 리포트', COUNT(*) FROM tb_analysis_report
UNION ALL
SELECT '요약 스냅샷', COUNT(*) FROM tb_analysis_summary_snapshot
UNION ALL
SELECT '인사이트 스냅샷', COUNT(*) FROM tb_analysis_insight_snapshot
UNION ALL
SELECT '솔루션 스냅샷', COUNT(*) FROM tb_analysis_solution_snapshot
UNION ALL
SELECT '채널 스냅샷', COUNT(*) FROM tb_analysis_channel_snapshot;

-- ========================================
-- 사용 방법
-- ========================================
-- 1. MySQL 클라이언트에서 실행:
--    mysql -u root -p < database_reset_data.sql
--
-- 2. 또는 MySQL Workbench에서:
--    파일 열기 → 실행
--
-- 3. 실행 후 브라우저에서:
--    자동분류 화면 → "초기화" 버튼 클릭
--    또는 F12 → Console → localStorage.clear() 입력
-- ========================================

