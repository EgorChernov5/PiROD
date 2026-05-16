-- Объединяет сдачи с заданиями для расчета распределения оценок.
WITH assignment_grades AS (
    SELECT
        a.course_id,
        a.assignment_id,
        a.title,
        a.max_score,
        s.grade,
        CASE WHEN s.grade = 0 THEN 1 ELSE 0 END AS is_zero,
        CASE WHEN CAST(s.submitted_ts AS date) > a.due_dt THEN 1 ELSE 0 END AS is_late
    FROM postgres.public.assignments AS a
    JOIN postgres.public.submissions AS s ON a.assignment_id = s.assignment_id
),
grade_stats AS (
    SELECT
        course_id,
        assignment_id,
        title,
        max_score,
        COUNT(*) AS submission_count,
        ROUND(AVG(CAST(grade AS double)), 2) AS avg_grade,
        ROUND(approx_percentile(CAST(grade AS double), 0.5), 2) AS median_grade,
        ROUND(AVG(CAST(is_zero AS double)), 3) AS zero_rate,
        ROUND(AVG(CAST(is_late AS double)), 3) AS late_rate
    FROM assignment_grades
    GROUP BY course_id, assignment_id, title, max_score
)
-- Помечает задания со слабым средним результатом и высокой долей просрочек.
SELECT
    course_id,
    assignment_id,
    title,
    submission_count,
    avg_grade,
    median_grade,
    zero_rate,
    late_rate,
    CASE
        WHEN avg_grade / CAST(max_score AS double) < 0.60 AND late_rate >= 0.40 THEN true
        ELSE false
    END AS is_too_hard
FROM grade_stats
ORDER BY is_too_hard DESC, avg_grade ASC, late_rate DESC, assignment_id;
