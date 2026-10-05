SELECT 'students' AS table_name, COUNT(*) AS row_count
FROM students
UNION ALL SELECT 'courses', COUNT(*) FROM courses
UNION ALL SELECT 'semesters', COUNT(*) FROM semesters
UNION ALL SELECT 'lecturers', COUNT(*) FROM lecturers
UNION ALL SELECT 'class_sections', COUNT(*) FROM class_sections
UNION ALL SELECT 'enrollments', COUNT(*) FROM enrollments;
SELECT code, name, credits
FROM courses
ORDER BY code;
SELECT code, name
FROM courses
WHERE LOWER(code) LIKE '%web%'
OR LOWER(name) LIKE '%web%'
ORDER BY code;
SELECT student_id, class_section_id
FROM enrollments
WHERE student_id = '22000001'
ORDER BY class_section_id;
SELECT s.name AS student_name,
cs.id AS class_id,
c.code AS course_code
FROM enrollments AS e
JOIN students AS s ON s.id = e.student_id
JOIN class_sections AS cs ON cs.id = e.class_section_id
JOIN courses AS c ON c.code = cs.course_code
WHERE s.id = '22000001'
ORDER BY cs.id;
SELECT cs.id AS class_id,
cs.course_code,
cs.capacity,
COUNT(e.student_id) AS enrolled,
cs.capacity - COUNT(e.student_id) AS remaining
FROM class_sections AS cs
LEFT JOIN enrollments AS e ON e.class_section_id = cs.id
GROUP BY cs.id, cs.course_code, cs.capacity
ORDER BY cs.id;
SELECT s.id, s.name
FROM students AS s
WHERE NOT EXISTS (
SELECT 1
FROM enrollments AS e
WHERE e.student_id = s.id
)
ORDER BY s.id;
WITH section_counts AS (
SELECT cs.id AS class_id,
cs.capacity,
COUNT(e.student_id) AS enrolled
FROM class_sections AS cs
LEFT JOIN enrollments AS e ON e.class_section_id = cs.id
GROUP BY cs.id, cs.capacity
)
SELECT class_id, capacity, enrolled,
capacity - enrolled AS remaining
FROM section_counts
WHERE enrolled < capacity
ORDER BY class_id;
WITH course_totals AS (
SELECT c.code, COUNT(e.student_id) AS total
FROM courses AS c
LEFT JOIN class_sections AS cs ON cs.course_code = c.code
LEFT JOIN enrollments AS e ON e.class_section_id = cs.id
GROUP BY c.code
)
SELECT code, total,
DENSE_RANK() OVER (ORDER BY total DESC) AS demand_rank
FROM course_totals
ORDER BY total DESC, code;