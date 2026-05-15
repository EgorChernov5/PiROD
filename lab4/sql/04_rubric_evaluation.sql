-- Разворачивает массив rubric из MongoDB и соединяет его со сдачами Postgres.
WITH rubric_items AS (
    SELECT
        a.course_id,
        s.assignment_id,
        s.submission_id,
        rubric.criterion AS criterion,
        CAST(rubric.points AS double) AS points,
        CAST(rubric.max_points AS double) AS max_points
    FROM postgres.public.submissions AS s
    JOIN postgres.public.assignments AS a ON s.assignment_id = a.assignment_id
    JOIN mongodb.university.submission_feedback AS f ON s.submission_id = f.submission_id
    CROSS JOIN UNNEST(f.rubric) AS rubric(criterion, max_points, points)
),
criterion_stats AS (
    SELECT
        criterion,
        COUNT(*) AS evaluation_count,
        ROUND(AVG(points), 2) AS avg_points,
        ROUND(AVG(points / NULLIF(max_points, 0)), 3) AS avg_score_ratio,
        ROUND(AVG(CASE WHEN points / NULLIF(max_points, 0) < 0.60 THEN CAST(1 AS double) ELSE CAST(0 AS double) END), 3) AS weak_rate
    FROM rubric_items
    GROUP BY criterion
)
-- Возвращает критерии с частыми просадками и их средние баллы.
SELECT
    criterion,
    evaluation_count,
    avg_points,
    avg_score_ratio,
    weak_rate
FROM criterion_stats
ORDER BY weak_rate DESC, avg_points ASC, criterion
LIMIT 10;
