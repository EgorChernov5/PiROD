-- Считает количество студентов и заданий по каждому курсу.
WITH student_counts AS (
    SELECT
        course_id,
        COUNT(DISTINCT student_id) AS student_count
    FROM postgres.public.enrollments
    GROUP BY course_id
),
assignment_counts AS (
    SELECT
        course_id,
        COUNT(*) AS assignment_count
    FROM postgres.public.assignments
    GROUP BY course_id
)
-- Возвращает топ-5 курсов по числу записанных студентов.
SELECT
    c.course_id,
    c.course_name,
    COALESCE(sc.student_count, 0) AS student_count,
    COALESCE(ac.assignment_count, 0) AS assignment_count
FROM postgres.public.courses AS c
LEFT JOIN student_counts AS sc ON c.course_id = sc.course_id
LEFT JOIN assignment_counts AS ac ON c.course_id = ac.course_id
ORDER BY student_count DESC, assignment_count DESC, c.course_id
LIMIT 5;
