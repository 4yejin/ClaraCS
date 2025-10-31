-- ClaraCS 자동 분류 기능 개선을 위한 DB 마이그레이션
-- 작성일: 2025-10-05
-- 실행 전 백업 필수!

USE clara_cs;

-- ============================================
-- 1. tb_ticket 테이블: 분류 결과 저장 컬럼 추가
-- ============================================
ALTER TABLE `tb_ticket`
  ADD COLUMN `classified_category_id` INT COMMENT 'AI가 분류한 카테고리 ID' AFTER `inquiry_type`,
  ADD COLUMN `classification_confidence` FLOAT COMMENT '분류 신뢰도 (0.0~1.0)' AFTER `classified_category_id`,
  ADD COLUMN `classification_keywords` JSON COMMENT '추출된 키워드 배열' AFTER `classification_confidence`,
  ADD COLUMN `classified_at` DATETIME COMMENT '분류 수행 시각' AFTER `classification_keywords`;

-- tb_ticket 인덱스 추가
CREATE INDEX idx_ticket_file_id ON tb_ticket(file_id);
CREATE INDEX idx_ticket_user_id ON tb_ticket(user_id);
CREATE INDEX idx_ticket_received_at ON tb_ticket(received_at);
CREATE INDEX idx_ticket_channel ON tb_ticket(channel);
CREATE INDEX idx_ticket_classified_category ON tb_ticket(classified_category_id);
CREATE INDEX idx_ticket_status ON tb_ticket(status);

-- ============================================
-- 2. tb_classification_result 테이블: 구조 변경
-- ============================================
-- 기존 테이블 백업 (데이터가 있다면)
CREATE TABLE IF NOT EXISTS `tb_classification_result_backup` LIKE `tb_classification_result`;
INSERT INTO `tb_classification_result_backup` SELECT * FROM `tb_classification_result`;

-- 기존 테이블 삭제 후 재생성
DROP TABLE IF EXISTS `tb_classification_result`;

CREATE TABLE `tb_classification_result` (
  `class_result_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '분류 결과 ID',
  `file_id` INT NOT NULL COMMENT '분류 대상 파일 ID',
  `user_id` INT NOT NULL COMMENT '분류 실행 사용자 ID',
  `engine_name` VARCHAR(100) COMMENT 'AI 엔진 이름 (GPT-4, Claude 등)',
  `total_tickets` INT COMMENT '분류된 총 티켓 수',
  `period_from` DATE COMMENT '분석 기간 시작일',
  `period_to` DATE COMMENT '분석 기간 종료일',
  `classified_at` DATETIME DEFAULT (NOW()) COMMENT '분류 실행 시각',
  `needs_review` BOOLEAN DEFAULT FALSE COMMENT '재검토 필요 여부'
) COMMENT='파일 단위 자동 분류 실행 정보';

-- tb_classification_result 인덱스 추가
CREATE INDEX idx_classification_file_id ON tb_classification_result(file_id);
CREATE INDEX idx_classification_user_id ON tb_classification_result(user_id);
CREATE INDEX idx_classification_date ON tb_classification_result(classified_at);

-- ============================================
-- 3. tb_classification_channel_result 테이블: 복합키 수정
-- ============================================
-- 기존 테이블 백업
CREATE TABLE IF NOT EXISTS `tb_classification_channel_result_backup` LIKE `tb_classification_channel_result`;
INSERT INTO `tb_classification_channel_result_backup` SELECT * FROM `tb_classification_channel_result`;

-- 기존 테이블 삭제 후 재생성
DROP TABLE IF EXISTS `tb_classification_channel_result`;

CREATE TABLE `tb_classification_channel_result` (
  `ch_result_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '채널 결과 ID',
  `class_result_id` INT COMMENT '분류 결과 ID (tb_classification_result 참조)',
  `channel` VARCHAR(64) COMMENT '채널명',
  `category_id` INT COMMENT '카테고리 ID',
  `count` INT DEFAULT 0 COMMENT '해당 채널+카테고리 티켓 수',
  `ratio` FLOAT COMMENT '비율'
) COMMENT='채널별 카테고리 분포 집계';

CREATE INDEX idx_channel_result_class_id ON tb_classification_channel_result(class_result_id);

-- ============================================
-- 4. 기타 테이블 인덱스 추가
-- ============================================

-- tb_uploaded_file 인덱스
CREATE INDEX idx_uploaded_file_user_id ON tb_uploaded_file(user_id);
CREATE INDEX idx_uploaded_file_status ON tb_uploaded_file(status);
CREATE INDEX idx_uploaded_file_created_at ON tb_uploaded_file(created_at);

-- tb_classification_category_result 인덱스
CREATE INDEX idx_category_result_class_id ON tb_classification_category_result(class_result_id);
CREATE INDEX idx_category_result_category_id ON tb_classification_category_result(category_id);

-- tb_classification_reliability_result 인덱스
CREATE INDEX idx_reliability_class_id ON tb_classification_reliability_result(class_result_id);

-- tb_analysis_report 인덱스
CREATE INDEX idx_report_file_id ON tb_analysis_report(file_id);
CREATE INDEX idx_report_created_by ON tb_analysis_report(created_by);
CREATE INDEX idx_report_status ON tb_analysis_report(status);

-- ============================================
-- 마이그레이션 완료
-- ============================================
-- 변경사항 확인 쿼리:
-- SHOW CREATE TABLE tb_ticket;
-- SHOW CREATE TABLE tb_classification_result;
-- SHOW CREATE TABLE tb_classification_channel_result;
-- SHOW INDEX FROM tb_ticket;

