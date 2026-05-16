-- Готовит строки сдач с задержкой в днях и флагом просрочки.
WITH submission_delays AS (
    SELECT
        a.course_id,
        st.group_name,
        s.submission_id,
        s.assignment_id,
        s.student_id,
        date_diff('day', a.due_dt, CAST(s.submitted_ts AS date)) AS delay_days,
        CASE WHEN CAST(s.submitted_ts AS date) > a.due_dt THEN 1 ELSE 0 END AS is_late
    FROM postgres.public.submissions AS s
    JOIN postgres.public.assignments AS a ON s.assignment_id = a.assignment_id
    JOIN postgres.public.students AS st ON s.student_id = st.student_id
)
-- Считает долю просрочек по курсам и учебным группам.
SELECT
    course_id,
    group_name,
    COUNT(*) AS submission_count,
    ROUND(AVG(CAST(GREATEST(delay_days, 0) AS double)), 2) AS avg_positive_delay_days,
    ROUND(AVG(CAST(is_late AS double)), 3) AS late_rate
FROM submission_delays
GROUP BY course_id, group_name
ORDER BY course_id, group_name;
