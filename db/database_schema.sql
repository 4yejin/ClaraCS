-- ClaraCS 데이터베이스 스키마
-- MySQL 8.0+

-- 데이터베이스 생성
CREATE DATABASE clara_cs;

USE clara_cs;

-- 테이블 생성
CREATE TABLE `tb_user` (
  `user_id` INT PRIMARY KEY AUTO_INCREMENT,
  `username` VARCHAR(150) NOT NULL,
  `email` VARCHAR(255) UNIQUE NOT NULL,
  `password_hash` VARCHAR(255),
  `role` VARCHAR(20) DEFAULT 'user',
  `created_at` DATETIME DEFAULT (NOW()),
  `updated_at` DATETIME
);

CREATE TABLE `tb_uploaded_file_extension_code` (
  `extension_code_id` INT PRIMARY KEY AUTO_INCREMENT,
  `extension_name` VARCHAR(16) NOT NULL,
  `description` VARCHAR(255)
);

CREATE TABLE `tb_file_batch` (
  `batch_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '배치 ID',
  `user_id` INT NOT NULL COMMENT '업로드한 사용자 ID',
  `batch_name` VARCHAR(255) COMMENT '배치 이름 (선택)',
  `file_count` INT DEFAULT 0 COMMENT '배치에 포함된 파일 수',
  `total_row_count` INT DEFAULT 0 COMMENT '전체 행 수',
  `status` VARCHAR(20) DEFAULT 'uploading' COMMENT '배치 상태: uploading, completed, processing, failed',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시각',
  `completed_at` DATETIME COMMENT '완료 시각',
  INDEX idx_batch_user_id (user_id),
  INDEX idx_batch_status (status),
  INDEX idx_batch_created_at (created_at)
) COMMENT '파일 배치 테이블 - 여러 파일을 하나의 그룹으로 관리';

CREATE TABLE `tb_uploaded_file` (
  `file_id` INT PRIMARY KEY AUTO_INCREMENT,
  `user_id` INT,
  `original_filename` VARCHAR(512) NOT NULL,
  `storage_path` VARCHAR(1024),
  `extension_code_id` INT,
  `row_count` INT,
  `status` VARCHAR(20) DEFAULT 'uploaded',
  `is_deleted` BOOLEAN,
  `deleted_at` DATETIME,
  `created_at` DATETIME DEFAULT (NOW()),
  `processed_at` DATETIME,
  `batch_id` INT COMMENT '파일이 속한 배치 ID',
  INDEX idx_uploaded_file_user_id (user_id),
  INDEX idx_uploaded_file_status (status),
  INDEX idx_uploaded_file_created_at (created_at),
  INDEX idx_uploaded_file_batch_id (batch_id)
);

CREATE TABLE `tb_column_mapping_code` (
  `mapping_code_id` INT PRIMARY KEY AUTO_INCREMENT,
  `code_name` VARCHAR(100) NOT NULL,
  `description` VARCHAR(255)
);

CREATE TABLE `tb_column_mapping` (
  `mapping_id` INT PRIMARY KEY AUTO_INCREMENT,
  `file_id` INT,
  `original_column` VARCHAR(255) NOT NULL,
  `mapping_code_id` INT,
  `is_activate` BOOLEAN,
  `created_at` DATETIME DEFAULT (NOW())
);

CREATE TABLE `tb_category` (
  `category_id` INT PRIMARY KEY AUTO_INCREMENT,
  `category_name` VARCHAR(150) NOT NULL,
  `parent_category_id` INT,
  `description` VARCHAR(255),
  `created_at` DATETIME DEFAULT (NOW())
);

CREATE TABLE `tb_ticket` (
  `ticket_id` INT PRIMARY KEY AUTO_INCREMENT,
  `file_id` INT,
  `user_id` INT,
  `received_at` DATETIME,
  `channel` VARCHAR(64),
  `customer_id` VARCHAR(128),
  `product_code` VARCHAR(128),
  `inquiry_type` VARCHAR(128),
  `classified_category_id` INT COMMENT 'AI가 분류한 카테고리 ID',
  `classification_confidence` FLOAT COMMENT '분류 신뢰도 (0.0~1.0)',
  `classification_keywords` JSON COMMENT '추출된 키워드 배열',
  `classified_at` DATETIME COMMENT '분류 수행 시각',
  `title` VARCHAR(1000),
  `body` TEXT,
  `assignee` VARCHAR(128),
  `status` VARCHAR(20) DEFAULT 'new',
  `created_at` DATETIME DEFAULT (NOW()),
  `updated_at` DATETIME,
  `raw_data` JSON,
  INDEX idx_ticket_file_id (file_id),
  INDEX idx_ticket_user_id (user_id),
  INDEX idx_ticket_received_at (received_at),
  INDEX idx_ticket_channel (channel),
  INDEX idx_ticket_classified_category (classified_category_id),
  INDEX idx_ticket_status (status)
);

CREATE TABLE `tb_classification_result` (
  `class_result_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '분류 결과 ID',
  `file_id` INT COMMENT '분류 대상 파일 ID (단일 파일)',
  `batch_id` INT COMMENT '분류 대상 배치 ID (배치)',
  `user_id` INT NOT NULL COMMENT '분류 실행 사용자 ID',
  `engine_name` VARCHAR(100) COMMENT 'AI 엔진 이름 (GPT-4, Claude 등)',
  `total_tickets` INT COMMENT '분류된 총 티켓 수',
  `period_from` DATE COMMENT '분석 기간 시작일',
  `period_to` DATE COMMENT '분석 기간 종료일',
  `classified_at` DATETIME DEFAULT (NOW()) COMMENT '분류 실행 시각',
  `needs_review` BOOLEAN DEFAULT FALSE COMMENT '재검토 필요 여부',
  INDEX idx_classification_file_id (file_id),
  INDEX idx_classification_batch_id (batch_id),
  INDEX idx_classification_user_id (user_id),
  INDEX idx_classification_date (classified_at)
);

CREATE TABLE `tb_classification_category_result` (
  `cat_result_id` INT PRIMARY KEY AUTO_INCREMENT,
  `class_result_id` INT,
  `category_id` INT,
  `count` INT DEFAULT 0,
  `ratio` FLOAT,
  `example_keywords` JSON,
  INDEX idx_category_result_class_id (class_result_id),
  INDEX idx_category_result_category_id (category_id)
);

CREATE TABLE `tb_classification_channel_result` (
  `ch_result_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '채널 결과 ID',
  `class_result_id` INT COMMENT '분류 결과 ID',
  `channel` VARCHAR(64) COMMENT '채널명',
  `category_id` INT COMMENT '카테고리 ID',
  `count` INT DEFAULT 0 COMMENT '해당 채널+카테고리 티켓 수',
  `ratio` FLOAT COMMENT '비율',
  INDEX idx_channel_result_class_id (class_result_id)
);

CREATE TABLE `tb_classification_reliability_result` (
  `reliability_id` INT PRIMARY KEY AUTO_INCREMENT,
  `class_result_id` INT,
  `metric_name` VARCHAR(128),
  `metric_value` FLOAT,
  `details` JSON,
  `created_at` DATETIME DEFAULT (NOW()),
  INDEX idx_reliability_class_id (class_result_id)
);

CREATE TABLE `tb_analysis_report` (
  `report_id` INT PRIMARY KEY AUTO_INCREMENT,
  `file_id` INT COMMENT '리포트 대상 파일 ID (단일 파일)',
  `batch_id` INT COMMENT '리포트 대상 배치 ID (배치)',
  `created_by` INT,
  `report_type` VARCHAR(50),
  `title` VARCHAR(255),
  `status` VARCHAR(20) DEFAULT 'queued',
  `file_path` VARCHAR(1024),
  `created_at` DATETIME DEFAULT (NOW()),
  `completed_at` DATETIME,
  INDEX idx_report_file_id (file_id),
  INDEX idx_report_batch_id (batch_id),
  INDEX idx_report_created_by (created_by),
  INDEX idx_report_status (status)
);

CREATE TABLE `tb_analysis_channel_snapshot` (
  `channel_snapshot_id` INT PRIMARY KEY AUTO_INCREMENT,
  `report_id` INT,
  `channel` VARCHAR(64),
  `time_period` DATE,
  `category_id` INT,
  `count` INT
);

CREATE TABLE `tb_analysis_summary_snapshot` (
  `summary_snapshot_id` INT PRIMARY KEY AUTO_INCREMENT,
  `report_id` INT,
  `total_tickets` INT,
  `resolved_count` JSON,
  `category_ratios` JSON,
  `repeat_rate` FLOAT,
  `created_at` DATETIME DEFAULT (NOW())
);

CREATE TABLE `tb_analysis_solution_snapshot` (
  `solution_id` INT PRIMARY KEY AUTO_INCREMENT,
  `report_id` INT,
  `solution_payload` JSON,
  `created_at` DATETIME DEFAULT (NOW())
);

CREATE TABLE `tb_analysis_insight_snapshot` (
  `insight_id` INT PRIMARY KEY AUTO_INCREMENT,
  `report_id` INT,
  `insight_payload` JSON,
  `created_at` DATETIME DEFAULT (NOW())
);