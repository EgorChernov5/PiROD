-- Удаляет старые таблицы при ручном повторном выполнении скрипта.
DROP TABLE IF EXISTS submissions;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS students;

-- Создает справочники студентов и преподавателей.
CREATE TABLE students (
    student_id INTEGER PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    group_name VARCHAR(20) NOT NULL,
    enrollment_year INTEGER NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE
);

CREATE TABLE teachers (
    teacher_id INTEGER PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    department VARCHAR(80) NOT NULL
);

-- Создает курсы и связи студентов с курсами.
CREATE TABLE courses (
    course_id INTEGER PRIMARY KEY,
    teacher_id INTEGER NOT NULL REFERENCES teachers(teacher_id),
    course_name VARCHAR(120) NOT NULL,
    semester VARCHAR(20) NOT NULL
);

CREATE TABLE enrollments (
    enrollment_id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(course_id),
    student_id INTEGER NOT NULL REFERENCES students(student_id),
    enrolled_dt DATE NOT NULL,
    UNIQUE (course_id, student_id)
);

-- Создает задания курса и факты сдачи работ.
CREATE TABLE assignments (
    assignment_id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(course_id),
    title VARCHAR(120) NOT NULL,
    due_dt DATE NOT NULL,
    max_score NUMERIC(5, 2) NOT NULL
);

CREATE TABLE submissions (
    submission_id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignments(assignment_id),
    student_id INTEGER NOT NULL REFERENCES students(student_id),
    submitted_ts TIMESTAMP NOT NULL,
    grade NUMERIC(5, 2) NOT NULL CHECK (grade >= 0),
    UNIQUE (assignment_id, student_id)
);
