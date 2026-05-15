-- Считает средний размер файлов по заданиям на основе manifest из MinIO.
WITH file_manifest AS (
    SELECT
        CAST(submission_id AS integer) AS submission_id,
        CAST(assignment_id AS integer) AS assignment_id,
        file_name,
        CAST(size_bytes AS bigint) AS size_bytes,
        object_path
    FROM minio.analytics.submission_files_manifest
)
SELECT
    assignment_id,
    COUNT(*) AS file_count,
    ROUND(AVG(size_bytes) / 1024.0, 2) AS avg_file_size_kb
FROM file_manifest
GROUP BY assignment_id
ORDER BY assignment_id;

-- Выводит топ-10 самых больших работ.
WITH file_manifest AS (
    SELECT
        CAST(submission_id AS integer) AS submission_id,
        CAST(assignment_id AS integer) AS assignment_id,
        file_name,
        CAST(size_bytes AS bigint) AS size_bytes,
        object_path
    FROM minio.analytics.submission_files_manifest
)
SELECT
    submission_id,
    assignment_id,
    file_name,
    size_bytes,
    object_path
FROM file_manifest
ORDER BY size_bytes DESC, submission_id
LIMIT 10;

-- Находит сдачи из Postgres, для которых нет файла в manifest MinIO.
WITH file_manifest AS (
    SELECT
        CAST(submission_id AS integer) AS submission_id,
        CAST(assignment_id AS integer) AS assignment_id
    FROM minio.analytics.submission_files_manifest
)
SELECT
    s.submission_id,
    s.assignment_id,
    s.student_id,
    s.submitted_ts,
    s.grade
FROM postgres.public.submissions AS s
LEFT JOIN file_manifest AS f
    ON s.submission_id = f.submission_id
    AND s.assignment_id = f.assignment_id
WHERE f.submission_id IS NULL
ORDER BY s.assignment_id, s.submission_id;
