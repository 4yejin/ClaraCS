-- ClaraCS 코드성 데이터 INSERT 쿼리
-- 작성일: 2025-10-05

USE clara_cs;

-- 1. tb_uploaded_file_extension_code (파일 확장자 코드)
INSERT INTO `tb_uploaded_file_extension_code` (`extension_name`, `description`) VALUES
('csv', 'CSV 파일 형식'),
('xlsx', 'Excel 파일 형식 (xlsx)'),
('xls', 'Excel 파일 형식 (xls)');

-- 2. tb_column_mapping_code (컬럼 매핑 코드)
-- 8개 필수 컬럼
INSERT INTO `tb_column_mapping_code` (`code_name`, `description`) VALUES
('접수일', '티켓 접수 날짜/시간'),
('고객ID', '고객 고유 식별자'),
('채널', 'CS 문의 채널 (전화, 이메일, 게시판 등)'),
('상품코드', '제품/상품 고유 코드'),
('문의 유형', '문의 카테고리/유형'),
('본문', '문의 내용 본문'),
('담당자', '처리 담당자'),
('처리 상태', '티켓 처리 상태');

-- 추가 컬럼 (필요시 사용)
INSERT INTO `tb_column_mapping_code` (`code_name`, `description`) VALUES
('제목', '문의 제목'),
('고객이메일', '고객 이메일 주소'),
('고객전화번호', '고객 전화번호'),
('우선순위', '티켓 처리 우선순위'),
('해결일시', '티켓 해결 완료 일시');

-- 3. tb_category (기본 카테고리 데이터 - 우선순위 기반)
-- 8개 카테고리 (우선순위 1-8)
INSERT INTO `tb_category` (`category_id`, `category_name`, `parent_category_id`, `description`) VALUES
(1, '품질/하자', NULL, '제품 품질 및 하자 관련 문의 (최우선 분류) - 불량, 파손, 오작동 등'),
(2, '서비스', NULL, '고객 서비스 및 응대 관련 문의 - 불친절, 응대 태도, 상담 불만 등'),
(3, '배송', NULL, '배송 및 물류 관련 문의 - 배송 지연, 택배 추적, 분실 등'),
(4, 'AS/수리', NULL, 'AS 및 제품 수리 관련 문의 - 수리 요청, 보증, 점검 등'),
(5, '결제', NULL, '결제, 환불, 취소 관련 문의 - 결제 오류, 환불 요청, 카드 승인 등'),
(6, '이벤트', NULL, '이벤트, 쿠폰, 프로모션 관련 문의 - 쿠폰 사용, 할인 행사 등'),
(7, '일반', NULL, '일반 문의 및 정보 요청 - 사용법, 계정, 로그인 등'),
(8, '기타', NULL, '분류되지 않은 기타 문의');

-- 4. tb_user (테스트 사용자 데이터)
INSERT INTO `tb_user` (`username`, `email`, `password_hash`, `role`) VALUES
('admin', 'admin@claraCS.com', 'hashed_password_here', 'admin'),
('cs_manager', 'manager@claraCS.com', 'hashed_password_here', 'manager'),
('cs_agent1', 'agent1@claraCS.com', 'hashed_password_here', 'user'),
('cs_agent2', 'agent2@claraCS.com', 'hashed_password_here', 'user');

-- 조회 쿼리 예시
-- SELECT * FROM tb_uploaded_file_extension_code;
-- SELECT * FROM tb_column_mapping_code;
-- SELECT * FROM tb_category WHERE parent_category_id IS NULL;  -- 대분류만
-- SELECT * FROM tb_category ORDER BY parent_category_id, category_id;  -- 전체
-- SELECT * FROM tb_user;

