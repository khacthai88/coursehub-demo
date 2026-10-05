INSERT INTO enrollments (student_id, class_section_id)
VALUES ('22000001', 'WEB-01');
INSERT INTO enrollments (student_id, class_section_id)
VALUES ('22999999', 'WEB-01');
UPDATE class_sections
SET capacity = 0
WHERE id = 'WEB-01';
UPDATE courses
SET credits = NULL
WHERE code = 'INT2204';
UPDATE students
SET email = 'anh@example.com'
WHERE id = '22000002';
UPDATE students
SET name = ' '
WHERE id = '22000004';