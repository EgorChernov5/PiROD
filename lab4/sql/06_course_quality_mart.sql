-- Агрегирует оценки и просрочки по курсам из Postgres.
WITH course_submission_stats AS (
    SELECT
        a.course_id,
        ROUND(AVG(CAST(s.grade AS double)), 2) AS avg_grade,
        ROUND(AVG(CASE WHEN CAST(s.submitted_ts AS date) > a.due_dt THEN CAST(1 AS double) ELSE CAST(0 AS double) END), 3) AS late_rate
    FROM postgres.public.assignments AS a
    JOIN postgres.public.submissions AS s ON a.assignment_id = s.assignment_id
    GROUP BY a.course_id
),
file_stats AS (
    SELECT
        a.course_id,
        ROUND(AVG(CAST(f.size_bytes AS bigint)) / 1024.0, 2) AS avg_file_size_kb
    FROM minio.analytics.submission_files_manifest AS f
    JOIN postgres.public.assignments AS a ON CAST(f.assignment_id AS integer) = a.assignment_id
    GROUP BY a.course_id
),
correctness_stats AS (
    SELECT
        a.course_id,
        ROUND(AVG(CAST(rubric.points AS double)), 2) AS avg_correctness_points
    FROM postgres.public.submissions AS s
    JOIN postgres.public.assignments AS a ON s.assignment_id = a.assignment_id
    JOIN mongodb.university.submission_feedback AS f ON s.submission_id = f.submission_id
    CROSS JOIN UNNEST(f.rubric) AS rubric(criterion, max_points, points)
    WHERE rubric.criterion = 'correctness'
    GROUP BY a.course_id
)
-- Собирает сквозную витрину качества курса по всем источникам.
SELECT
    c.course_id,
    c.course_name,
    css.avg_grade,
    css.late_rate,
    fs.avg_file_size_kb,
    cs.avg_correctness_points
FROM postgres.public.courses AS c
LEFT JOIN course_submission_stats AS css ON c.course_id = css.course_id
LEFT JOIN file_stats AS fs ON c.course_id = fs.course_id
LEFT JOIN correctness_stats AS cs ON c.course_id = cs.course_id
ORDER BY c.course_id;
