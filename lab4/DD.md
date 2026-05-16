# Отчет по архиву model4_university

## Структура архива

```
model4_university/
  minio/
    submission_files_manifest.csv
  mongodb/
    submission_feedback.csv
  postgres/
    assignments.csv
    courses.csv
    enrollments.csv
    students.csv
    submissions.csv
    teachers.csv
```

## Файл `minio/submission_files_manifest.csv`

- Строк: 1562
- Колонок: 5
- Колонки: assignment_id, student_id, submission_id, file_path, size_kb

### Пример данных

|   assignment_id |   student_id |   submission_id | file_path                                                         |   size_kb |
|----------------:|-------------:|----------------:|:------------------------------------------------------------------|----------:|
|               1 |           21 |               1 | submissions_files/assignment_id=1/student_id=21/submission_1.zip  |      4314 |
|               1 |           31 |               2 | submissions_files/assignment_id=1/student_id=31/submission_2.zip  |      3590 |
|               1 |           67 |               3 | submissions_files/assignment_id=1/student_id=67/submission_3.zip  |      4881 |
|               1 |          118 |               4 | submissions_files/assignment_id=1/student_id=118/submission_4.zip |      4371 |
|               1 |           40 |               5 | submissions_files/assignment_id=1/student_id=40/submission_5.zip  |      1191 |

## Файл `mongodb/submission_feedback.csv`

- Строк: 900
- Колонок: 6
- Колонки: _id, submission_id, teacher_id, ts, rubric, overall_comment

### Пример данных

| _id             |   submission_id |   teacher_id | ts                  | rubric                                                                                                                                                                                                                                        | overall_comment   |
|:----------------|----------------:|-------------:|:--------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------|
| fb_wkrrvaogrynz |            1297 |           13 | 2025-02-17 02:36:49 | [{"criterion": "correctness", "points": 2, "comment": "ok"}, {"criterion": "report", "points": 3, "comment": "excellent"}, {"criterion": "style", "points": 1, "comment": "ok"}, {"criterion": "tests", "points": 2, "comment": "excellent"}] | Great solution    |
| fb_nflyrmrifwvh |            1504 |            4 | 2025-02-03 07:15:18 | [{"criterion": "report", "points": 5, "comment": "excellent"}, {"criterion": "correctness", "points": 4, "comment": "good"}, {"criterion": "style", "points": 0, "comment": "needs work"}]                                                    | Incomplete        |
| fb_mnihbpxcvwnt |             539 |           10 | 2025-03-12 11:48:34 | [{"criterion": "report", "points": 2, "comment": "good"}, {"criterion": "style", "points": 4, "comment": "missing"}]                                                                                                                          | Please improve    |
| fb_tsnbtklemwqc |             146 |           11 | 2025-07-26 05:22:16 | [{"criterion": "report", "points": 0, "comment": "needs work"}, {"criterion": "tests", "points": 3, "comment": "missing"}, {"criterion": "performance", "points": 3, "comment": "ok"}]                                                        | Please improve    |
| fb_tpgmzgorebcu |             944 |            7 | 2025-06-09 22:23:22 | [{"criterion": "style", "points": 5, "comment": "needs work"}, {"criterion": "tests", "points": 0, "comment": "needs work"}, {"criterion": "performance", "points": 1, "comment": "needs work"}]                                              | Nice work         |

## Файл `postgres/assignments.csv`

- Строк: 70
- Колонок: 4
- Колонки: assignment_id, course_id, due_dt, max_score

### Пример данных

|   assignment_id |   course_id | due_dt     |   max_score |
|----------------:|------------:|:-----------|------------:|
|               1 |           9 | 2025-04-08 |          30 |
|               2 |          19 | 2025-02-27 |          30 |
|               3 |          23 | 2025-12-04 |          30 |
|               4 |           6 | 2025-10-18 |          20 |
|               5 |          18 | 2025-06-28 |          10 |

## Файл `postgres/courses.csv`

- Строк: 28
- Колонок: 4
- Колонки: course_id, title, teacher_id, semester

### Пример данных

|   course_id | title    |   teacher_id | semester    |
|------------:|:---------|-------------:|:------------|
|           1 | Course_1 |            3 | 2025-Fall   |
|           2 | Course_2 |            3 | 2024-Fall   |
|           3 | Course_3 |            4 | 2024-Fall   |
|           4 | Course_4 |           10 | 2024-Fall   |
|           5 | Course_5 |           10 | 2025-Spring |

## Файл `postgres/enrollments.csv`

- Строк: 620
- Колонок: 3
- Колонки: student_id, course_id, enrolled_dt

### Пример данных

|   student_id |   course_id | enrolled_dt   |
|-------------:|------------:|:--------------|
|            1 |          28 | 2025-07-21    |
|            1 |          17 | 2025-04-13    |
|            1 |           6 | 2025-01-25    |
|            1 |           7 | 2025-01-16    |
|            1 |          24 | 2025-07-09    |

## Файл `postgres/students.csv`

- Строк: 140
- Колонок: 4
- Колонки: student_id, name, group_name, enrollment_year

### Пример данных

|   student_id | name      | group_name   |   enrollment_year |
|-------------:|:----------|:-------------|------------------:|
|            1 | Student_1 | CS-4-C       |              2021 |
|            2 | Student_2 | CS-1-B       |              2022 |
|            3 | Student_3 | CS-2-B       |              2024 |
|            4 | Student_4 | CS-4-C       |              2024 |
|            5 | Student_5 | CS-3-B       |              2021 |

## Файл `postgres/submissions.csv`

- Строк: 1562
- Колонок: 5
- Колонки: submission_id, assignment_id, student_id, submitted_ts, score

### Пример данных

|   submission_id |   assignment_id |   student_id | submitted_ts        |   score |
|----------------:|----------------:|-------------:|:--------------------|--------:|
|               1 |               1 |           21 | 2025-04-08 10:03:09 |      27 |
|               2 |               1 |           31 | 2025-04-08 03:19:38 |      25 |
|               3 |               1 |           67 | 2025-04-06 01:38:51 |      24 |
|               4 |               1 |          118 | 2025-04-03 14:08:28 |      29 |
|               5 |               1 |           40 | 2025-04-11 10:01:55 |      26 |

## Файл `postgres/teachers.csv`

- Строк: 16
- Колонок: 3
- Колонки: teacher_id, name, department

### Пример данных

|   teacher_id | name      | department   |
|-------------:|:----------|:-------------|
|            1 | Teacher_1 | SE           |
|            2 | Teacher_2 | SE           |
|            3 | Teacher_3 | AI           |
|            4 | Teacher_4 | SE           |
|            5 | Teacher_5 | SE           |

## Связи между данными

- students.csv ↔ enrollments.csv: связь студентов и курсов
- courses.csv ↔ teachers.csv: курсы и преподаватели
- assignments.csv ↔ submissions.csv: задания и сдачи
- submission_feedback.csv: обратная связь по сдачам
- submission_files_manifest.csv: файлы, связанные со сдачами