-- Тестовые данные для БД университета

-- ФАКУЛЬТЕТЫ
INSERT INTO faculties (faculty_code, faculty_name, dean_name) VALUES
    ('К', 'Космический факультет', 'Поярков Н.Г.'),
    ('Л', 'Лесное хозяйство', 'Лавренов М.А.');

-- КАФЕДРЫ
INSERT INTO departments (dept_code, dept_name, faculty_id) VALUES
    ('К1', 'Системы автоматического управления', 1),
    ('К2', 'Информационно-измерительные системы', 1),
    ('К3', 'Прикладная математика и информатика', 1),
    ('ЛТ1', 'Химическая технология древесины', 2),
    ('ЛТ2', 'Лесоводство и защита леса', 2);

-- ТИПЫ КОНТРОЛЯ
INSERT INTO control_types (control_code, control_name) VALUES
    ('кур', 'Курсовая работа'),
    ('зач', 'Зачёт'),
    ('экз', 'Экзамен'),
    ('прк', 'Практика');

-- ГРУППЫ
INSERT INTO groups (group_code, faculty_id, enrollment_year, specialty_name) VALUES
    ('К3-36Б', 1, 2023, 'Информатика и ВТ'),
    ('К1-48Б', 1, 2022, 'Системы управления'),
    ('ЛТ2-24Л', 2, 2024, 'Лесоводство');

-- ДИСЦИПЛИНЫ
INSERT INTO disciplines (discipline_name, dept_id) VALUES
    ('Базы данных', 3),
    ('Теория автоматического управления', 1),
    ('Метрология', 2),
    ('Дендрология', 5),
    ('Органическая химия', 4);

-- УЧЕБНЫЙ ПЛАН
INSERT INTO discipline_control (discipline_id, control_type_id, course, half_year) VALUES
    (1, 3, 3, 2),  -- (id предмета, id типа контроля, курс, полугодие) -- 3 курс + 2 полугодие = 6 семестр
    (2, 3, 4, 2),
    (3, 2, 3, 2),
    (4, 3, 2, 2),
    (5, 3, 1, 2);

-- СТУДЕНТЫ (по 5 в группу)
INSERT INTO students (full_name, record_book_num, group_id, enrollment_date, status) VALUES
    ('Иванов Александр Александрович', '22МК301', 1, '2023-09-01', 'active'),
    ('Петров Дмитрий Дмитриевич', '22МК302', 1, '2023-09-01', 'active'),
    ('Сидорова Анна Алексеевна', '22МК303', 1, '2023-09-01', 'active'),
    ('Смирнов Сергей Андреевич', '22МК304', 1, '2023-09-01', 'academic_leave'),
    ('Кузнецова Елена Игоревна', '22МК305', 1, '2023-09-01', 'expelled'),
    ('Попов Алексей Иванович', '22МК101', 2, '2022-09-01', 'active'),
    ('Васильев Артем Михайлович', '22МК102', 2, '2022-09-01', 'active'),
    ('Михайлова Мария Павловна', '22МК103', 2, '2022-09-01', 'active'),
    ('Новиков Никита Владимирович', '22МК104', 2, '2022-09-01', 'active'),
    ('Федорова Ольга Николаевна', '22МК105', 2, '2022-09-01', 'active'),
    ('Морозов Егор Олегович', '22ЛТ201', 3, '2024-09-01', 'active'),
    ('Волков Даниил Игоревич', '22ЛТ202', 3, '2024-09-01', 'active'),
    ('Алексеева Дарья Дмитриевна', '22ЛТ203', 3, '2024-09-01', 'active'),
    ('Лебедев Владислав Павлович', '22ЛТ204', 3, '2024-09-01', 'active'),
    ('Семенова София Сергеевна', '22ЛТ205', 3, '2024-09-01', 'active');

-- ОЦЕНКИ (только для студентов, которые не в академе, не отчислены)
INSERT INTO grades (student_id, discipline_control_id, semester, grade_value, grade_date)
SELECT s.student_id, dc.discipline_control_id, dc.semester,
       CASE WHEN random() < 0.7 THEN '5' WHEN random() < 0.9 THEN '4' ELSE '3' END,
       CURRENT_DATE - (random() * 365)::INT
FROM students s
JOIN groups g ON s.group_id = g.group_id
JOIN faculties f ON g.faculty_id = f.faculty_id
JOIN departments dep ON f.faculty_id = dep.faculty_id
JOIN disciplines d ON dep.dept_id = d.dept_id
JOIN discipline_control dc ON d.discipline_id = dc.discipline_id
WHERE s.status = 'active'
ON CONFLICT DO NOTHING;

-- ПРИВЯЗКА ПОЛЬЗОВАТЕЛЕЙ
INSERT INTO user_student (user_login, student_id) VALUES
    ('ivanov', 1),
    ('petrov', 2),
    ('sidorov', 3);
