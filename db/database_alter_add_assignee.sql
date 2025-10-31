-- tb_ticket 테이블에 assignee 컬럼 추가
-- 실행일: 2025-10-06

USE clara_cs;

-- assignee 컬럼 추가 (담당자)
ALTER TABLE tb_ticket 
ADD COLUMN assignee VARCHAR(128) AFTER body;

-- 확인
DESCRIBE tb_ticket;

-- 데이터 확인
SELECT ticket_id, file_id, customer_id, channel, assignee, status, created_at 
FROM tb_ticket 
ORDER BY created_at DESC 
LIMIT 10;

