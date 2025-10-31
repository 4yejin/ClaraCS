-- 새로운 카테고리 구조로 업데이트
-- 작성일: 2025-10-18
-- 설명: 8개 카테고리 우선순위 기반 분류 시스템

USE clara_cs;

-- 기존 카테고리 데이터 삭제
TRUNCATE tb_category;

-- 새로운 카테고리 데이터 삽입 (우선순위 기반)
-- 기존 데이터와 충돌하지 않도록 INSERT IGNORE 사용

-- 1순위: 품질/하자
INSERT IGNORE INTO `tb_category` (`category_id`, `category_name`, `parent_category_id`, `description`) 
VALUES (1, '품질/하자', NULL, '제품 품질 및 하자 관련 문의 (최우선 분류)');

-- 2순위: 서비스
INSERT IGNORE INTO `tb_category` (`category_id`, `category_name`, `parent_category_id`, `description`) 
VALUES (2, '서비스', NULL, '고객 서비스 및 응대 관련 문의');

-- 3순위: 배송
INSERT IGNORE INTO `tb_category` (`category_id`, `category_name`, `parent_category_id`, `description`) 
VALUES (3, '배송', NULL, '배송 및 물류 관련 문의');

-- 4순위: AS/수리
INSERT IGNORE INTO `tb_category` (`category_id`, `category_name`, `parent_category_id`, `description`) 
VALUES (4, 'AS/수리', NULL, 'AS 및 제품 수리 관련 문의');

-- 5순위: 결제
INSERT IGNORE INTO `tb_category` (`category_id`, `category_name`, `parent_category_id`, `description`) 
VALUES (5, '결제', NULL, '결제, 환불, 취소 관련 문의');

-- 6순위: 이벤트
INSERT IGNORE INTO `tb_category` (`category_id`, `category_name`, `parent_category_id`, `description`) 
VALUES (6, '이벤트', NULL, '이벤트, 쿠폰, 프로모션 관련 문의');

-- 7순위: 일반
INSERT IGNORE INTO `tb_category` (`category_id`, `category_name`, `parent_category_id`, `description`) 
VALUES (7, '일반', NULL, '일반 문의 및 정보 요청');

-- 8순위: 기타
INSERT IGNORE INTO `tb_category` (`category_id`, `category_name`, `parent_category_id`, `description`) 
VALUES (8, '기타', NULL, '분류되지 않은 기타 문의');

-- 조회 확인
SELECT * FROM tb_category WHERE parent_category_id IS NULL ORDER BY category_id;

-- 참고: 기존 티켓 데이터의 category_id도 함께 업데이트해야 할 수 있습니다.
-- 필요시 다음 쿼리를 실행하세요:
-- UPDATE tb_ticket SET category_id = NULL WHERE category_id NOT IN (1,2,3,4,5,6,7,8);

