-- Создает staging-таблицу для студентов из архивного CSV.
CREATE TEMP TABLE raw_students (
    student_id INTEGER,
    name VARCHAR(120),
    group_name VARCHAR(20),
    enrollment_year INTEGER
);

COPY raw_students
FROM '/seed-data/postgres/students.csv'
WITH (FORMAT csv, HEADER true);

-- Загружает студентов в рабочую модель Postgres.
INSERT INTO students (student_id, full_name, group_name, enrollment_year, email)
SELECT
    student_id,
    name,
    group_name,
    enrollment_year,
    CONCAT('student', student_id, '@example.edu') AS email
FROM raw_students;

-- Создает staging-таблицу для преподавателей из архивного CSV.
CREATE TEMP TABLE raw_teachers (
    teacher_id INTEGER,
    name VARCHAR(120),
    department VARCHAR(80)
);

COPY raw_teachers
FROM '/seed-data/postgres/teachers.csv'
WITH (FORMAT csv, HEADER true);

-- Загружает преподавателей в рабочую модель Postgres.
INSERT INTO teachers (teacher_id, full_name, department)
SELECT
    teacher_id,
    name,
    department
FROM raw_teachers;

-- Создает staging-таблицу для курсов из архивного CSV.
CREATE TEMP TABLE raw_courses (
    course_id INTEGER,
    title VARCHAR(120),
    teacher_id INTEGER,
    semester VARCHAR(20)
);

COPY raw_courses
FROM '/seed-data/postgres/courses.csv'
WITH (FORMAT csv, HEADER true);

-- Загружает курсы в рабочую модель Postgres.
INSERT INTO courses (course_id, teacher_id, course_name, semester)
SELECT
    course_id,
    teacher_id,
    title,
    semester
FROM raw_courses;

-- Создает staging-таблицу для записей на курсы из архивного CSV.
CREATE TEMP TABLE raw_enrollments (
    student_id INTEGER,
    course_id INTEGER,
    enrolled_dt DATE
);

COPY raw_enrollments
FROM '/seed-data/postgres/enrollments.csv'
WITH (FORMAT csv, HEADER true);

-- Загружает записи на курсы с синтетическим enrollment_id.
INSERT INTO enrollments (enrollment_id, course_id, student_id, enrolled_dt)
SELECT
    ROW_NUMBER() OVER (ORDER BY course_id, student_id, enrolled_dt) AS enrollment_id,
    course_id,
    student_id,
    enrolled_dt
FROM (
    SELECT DISTINCT
        student_id,
        course_id,
        enrolled_dt
    FROM raw_enrollments
) AS distinct_enrollments;

-- Создает staging-таблицу для заданий из архивного CSV.
CREATE TEMP TABLE raw_assignments (
    assignment_id INTEGER,
    course_id INTEGER,
    due_dt DATE,
    max_score NUMERIC(5, 2)
);

COPY raw_assignments
FROM '/seed-data/postgres/assignments.csv'
WITH (FORMAT csv, HEADER true);

-- Загружает задания с синтетическим названием.
INSERT INTO assignments (assignment_id, course_id, title, due_dt, max_score)
SELECT
    assignment_id,
    course_id,
    CONCAT('Assignment_', assignment_id) AS title,
    due_dt,
    max_score
FROM raw_assignments;

-- Создает staging-таблицу для сдач из архивного CSV.
CREATE TEMP TABLE raw_submissions (
    submission_id INTEGER,
    assignment_id INTEGER,
    student_id INTEGER,
    submitted_ts TIMESTAMP,
    score NUMERIC(5, 2)
);

COPY raw_submissions
FROM '/seed-data/postgres/submissions.csv'
WITH (FORMAT csv, HEADER true);

-- Загружает сдачи, переименовывая score в grade.
INSERT INTO submissions (submission_id, assignment_id, student_id, submitted_ts, grade)
SELECT
    submission_id,
    assignment_id,
    student_id,
    submitted_ts,
    score AS grade
FROM raw_submissions;
