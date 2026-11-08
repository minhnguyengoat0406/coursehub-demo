SELECT 'students' AS table_name, COUNT(*) AS row_count
FROM students
UNION ALL SELECT 'courses', COUNT(*) FROM courses
UNION ALL SELECT 'semesters', COUNT(*) FROM semesters
UNION ALL SELECT 'lecturers', COUNT(*) FROM lecturers
UNION ALL SELECT 'class_sections', COUNT(*) FROM class_sections
UNION ALL SELECT 'enrollments', COUNT(*) FROM enrollments;

-- Q1: Hien thi danh sach hoc phan
SELECT code, name, credits
FROM courses
ORDER BY code;

-- Q2: Tim hoc phan theo mot phan ma hoac ten
SELECT code, name
FROM courses
WHERE LOWER(code) LIKE '%web%'
   OR LOWER(name) LIKE '%web%'
ORDER BY code;

-- Q3a: Xem ma cac lop Minh Anh da dang ky
SELECT student_id, class_section_id
FROM enrollments
WHERE student_id = '22000001'
ORDER BY class_section_id;

-- Q3: Xem chi tiet cac lop Minh Anh da dang ky
SELECT s.full_name AS student_name,
    cs.id AS class_id,
    c.code AS course_code
FROM enrollments AS e
JOIN students AS s ON s.id = e.student_id
JOIN class_sections AS cs ON cs.id = e.class_section_id
JOIN courses AS c ON c.code = cs.course_code
WHERE s.id = '22000001'
ORDER BY cs.id;

-- Q4: Dem so sinh vien va so cho con lai cua tung lop
SELECT cs.id AS class_id,
    cs.course_code,
    cs.capacity,
    COUNT(e.student_id) AS enrolled,
    cs.capacity - COUNT(e.student_id) AS remaining
FROM class_sections AS cs
LEFT JOIN enrollments AS e ON e.class_section_id = cs.id
GROUP BY cs.id, cs.course_code, cs.capacity
ORDER BY cs.id;

-- Q5: Tim sinh vien chua dang ky lop nao
SELECT s.id, s.full_name
FROM students AS s
WHERE NOT EXISTS (
    SELECT 1
    FROM enrollments AS e
    WHERE e.student_id = s.id
)
ORDER BY s.id;

-- Q6: Dung CTE de lay cac lop con cho
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

-- Q7: Xep hang hoc phan theo so luot dang ky
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