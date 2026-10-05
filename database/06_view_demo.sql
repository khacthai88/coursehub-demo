BEGIN;
INSERT INTO enrollments (student_id, class_section_id)
VALUES ('22000004', 'WEB-01');
SELECT class_id, capacity, enrolled, remaining
FROM v_section_summary
WHERE class_id = 'WEB-01';
ROLLBACK;
SELECT class_id, capacity, enrolled, remaining
FROM v_section_summary
WHERE class_id = 'WEB-01';