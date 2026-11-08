-- 1. Dang ky trung mot lop
INSERT INTO enrollments (student_id, class_section_id)
VALUES ('22000001', 'WEB-01');

-- 2. Dang ky cho sinh vien khong ton tai
INSERT INTO enrollments (student_id, class_section_id)
VALUES ('22999999', 'WEB-01');

-- 3. Doi suc chua lop thanh 0
UPDATE class_sections
SET capacity = 0
WHERE id = 'WEB-01';

-- 4. Bo trong so tin chi
UPDATE courses
SET credits = NULL
WHERE code = 'INT2204';

-- 5. Dung lai email cua sinh vien khac
UPDATE students
SET email = 'anh@example.com'
WHERE id = '22000002';