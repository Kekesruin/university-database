-- Структура БД университета
-- Автор: Федоров М.Ю., 2026

DROP TABLE IF EXISTS grades CASCADE;
DROP TABLE IF EXISTS discipline_control CASCADE;
DROP TABLE IF EXISTS disciplines CASCADE;
DROP TABLE IF EXISTS departments CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS groups CASCADE;
DROP TABLE IF EXISTS control_types CASCADE;
DROP TABLE IF EXISTS faculties CASCADE;
DROP TABLE IF EXISTS user_student CASCADE;

CREATE TABLE faculties (
    faculty_id SERIAL PRIMARY KEY,
    faculty_code VARCHAR(5) UNIQUE NOT NULL,
    faculty_name VARCHAR(100) NOT NULL,
    dean_name VARCHAR(100)
);

CREATE TABLE control_types (
    control_type_id SERIAL PRIMARY KEY,
    control_code VARCHAR(10) UNIQUE NOT NULL,
    control_name VARCHAR(50) NOT NULL
);

CREATE TABLE groups (
    group_id SERIAL PRIMARY KEY,
    group_code VARCHAR(20) UNIQUE NOT NULL,
    faculty_id INT NOT NULL,
    enrollment_year INT,
    specialty_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    closed_date DATE,
    CONSTRAINT fk_groups_faculty FOREIGN KEY (faculty_id) REFERENCES faculties(faculty_id)
);

CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    record_book_num VARCHAR(20) UNIQUE,
    group_id INT NOT NULL,
    birth_date DATE,
    phone VARCHAR(20),
    email VARCHAR(100),
    enrollment_date DATE DEFAULT CURRENT_DATE,
    education_form VARCHAR(20) DEFAULT 'Очная',
    education_basis VARCHAR(20) DEFAULT 'Бюджет',
    status VARCHAR(20) DEFAULT 'active',
    expelled_date DATE,
    expulsion_reason TEXT,
    CONSTRAINT fk_students_group FOREIGN KEY (group_id) REFERENCES groups(group_id)
);

CREATE TABLE departments (
    dept_id SERIAL PRIMARY KEY,
    dept_code VARCHAR(5) UNIQUE NOT NULL,
    dept_name VARCHAR(100),
    faculty_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    closed_date DATE,
    CONSTRAINT fk_departments_faculty FOREIGN KEY (faculty_id) REFERENCES faculties(faculty_id) ON DELETE SET NULL
);

CREATE TABLE disciplines (
    discipline_id SERIAL PRIMARY KEY,
    discipline_name VARCHAR(100) NOT NULL,
    dept_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    closed_date DATE,
    CONSTRAINT fk_disciplines_department FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE discipline_control (
    discipline_control_id SERIAL PRIMARY KEY,
    discipline_id INT NOT NULL,
    control_type_id INT NOT NULL,
    course INT CHECK (course BETWEEN 1 AND 6),
    half_year INT CHECK (half_year IN (1, 2)),
    semester INT GENERATED ALWAYS AS ((course - 1) * 2 + half_year) STORED,
    CONSTRAINT fk_dc_discipline FOREIGN KEY (discipline_id) REFERENCES disciplines(discipline_id),
    CONSTRAINT fk_dc_control FOREIGN KEY (control_type_id) REFERENCES control_types(control_type_id),
    UNIQUE(discipline_id, control_type_id, semester)
);

CREATE TABLE grades (
    grade_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL,
    discipline_control_id INT NOT NULL,
    semester INT NOT NULL,
    grade_value VARCHAR(10) NOT NULL,
    grade_date DATE DEFAULT CURRENT_DATE,
    CONSTRAINT fk_grades_student FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_grades_dc FOREIGN KEY (discipline_control_id) REFERENCES discipline_control(discipline_control_id),
    UNIQUE(student_id, discipline_control_id, semester)
);

CREATE TABLE user_student (
    user_login VARCHAR(100) PRIMARY KEY,
    student_id INT UNIQUE NOT NULL REFERENCES students(student_id)
);

CREATE FUNCTION get_current_semester(
    p_enrollment_year INT,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS INT AS $$
DECLARE
    v_year INT 	:= EXTRACT(YEAR FROM p_date);
    v_month INT := EXTRACT(MONTH FROM p_date);
    years_passed INT;
    semester INT;
BEGIN
    years_passed := v_year - p_enrollment_year;

    IF v_month BETWEEN 9 AND 12 THEN
        semester := years_passed * 2 + 1;
    ELSIF v_month BETWEEN 1 AND 2 THEN
        semester := (years_passed - 1) * 2 + 1;
    ELSIF v_month BETWEEN 3 AND 8 THEN
        semester := (years_passed - 1) * 2 + 2;
    END IF;

    RETURN semester;
END;
$$ LANGUAGE plpgsql;

CREATE VIEW v_my_grades AS
SELECT 
    d.discipline_name AS "Предмет",
    ct.control_name AS "Тип",
    gr.semester AS "Семестр",
    gr.grade_value AS "Оценка",
    gr.grade_date AS "Дата"
FROM grades gr
JOIN students s ON gr.student_id = s.student_id
JOIN discipline_control dc ON gr.discipline_control_id = dc.discipline_control_id
JOIN disciplines d ON dc.discipline_id = d.discipline_id
JOIN control_types ct ON dc.control_type_id = ct.control_type_id
JOIN user_student us ON s.student_id = us.student_id
WHERE us.user_login = CURRENT_USER;

CREATE VIEW v_teacher_groups AS
SELECT 
    g.group_code AS "Группа",
    s.student_id AS "ID",
    s.full_name AS "ФИО",
    s.record_book_num AS "Зачётка",
    s.status AS "Статус"
FROM students s
JOIN groups g ON s.group_id = g.group_id;

CREATE VIEW v_teacher_grades AS
SELECT 
    g.group_code AS "Группа",
    s.full_name AS "ФИО",
    d.discipline_name AS "Предмет",
    ct.control_name AS "Тип",
    gr.semester AS "Семестр",
    gr.grade_value AS "Оценка",
    gr.grade_date AS "Дата",
    gr.grade_id
FROM grades gr
JOIN students s ON gr.student_id = s.student_id
JOIN groups g ON s.group_id = g.group_id
JOIN discipline_control dc ON gr.discipline_control_id = dc.discipline_control_id
JOIN disciplines d ON dc.discipline_id = d.discipline_id
JOIN control_types ct ON dc.control_type_id = ct.control_type_id;
