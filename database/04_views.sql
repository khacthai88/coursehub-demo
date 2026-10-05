CREATE VIEW v_section_summary AS
SELECT cs.id AS class_id,
cs.course_code,
cs.capacity,
COUNT(e.student_id) AS enrolled,
cs.capacity - COUNT(e.student_id) AS remaining
FROM class_sections AS cs
LEFT JOIN enrollments AS e ON e.class_section_id = cs.id
GROUP BY cs.id, cs.course_code, cs.capacity;
SELECT class_id, course_code, capacity, enrolled, remaining
FROM v_section_summary
ORDER BY class_id;
SELECT class_id, remaining
FROM v_section_summary
WHERE remaining > 0
ORDER BY class_id;