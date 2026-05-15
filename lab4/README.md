# PiROD
Лабораторная работа 4.

# Задание
## Принципы работы с Trino

В рамках данной работы вы познакомитесь с инструментом Trino, который позволяет производить запросы к данным, хранящимся на различных источниках.

Этапы выполнения:
- Развернуть с помощью docker compose 3 хранилища: Postgres, Minio, Mongodb.
- Загрузить данные в соответствующие хранилища в соответствии с моделью данных.
- Выполнить задачи. Итогом работы должен быть отчет и приложенные к нему SQL скрипты. Каждый отдельный скрипт должен решать одну конкретную задачу.

### Варинат 4. Университет: курсы, задания, сдачи, фидбек, файлы

Хранилища:
- Postgres: students, teachers, courses, enrollments, assignments, submissions
- MongoDB: submission_feedback (rubric JSON)
- MinIO: submission_files_manifest

Задачи:
1. Нагрузка курсов (Postgres). Для каждого course_id посчитать число студентов (enrollments) и число заданий. Вывести топ-5 курсов по числу студентов.
2. Пунктуальность сдач (Postgres). JOIN submissions ↔ assignments: delay_days = date(submitted_ts) - due_dt. Посчитать долю просрочек по курсам и по группам.
3. Распределение оценок (Postgres). По каждому заданию: средняя оценка, медиана, доля нулей. Найти задания `слишком сложные` (низкий mean и высокая доля просрочек).
4. Оценивание по рубрике (Postgres <-> Mongo). Распарсить rubric (массив критериев) и вывести:
    - средний points по критериям (correctness/style/tests/…)
    - топ-критерии, где чаще всего просадки
5. Файлы работ (MinIO). Для каждого задания: средний размер файла, топ-10 самых больших работ. Проверить `есть submission, но нет файла` (JOIN submissions <-> manifest).
6. Сквозная витрина качества курса. Для каждого course_id:
    - средняя оценка
    - доля просрочек
    - средний размер файла
    - средний балл по correctness (из rubric)

# Решение

## Docker-образы

- Docker образ Postgres - [postgres](https://hub.docker.com/_/postgres).
- Docker образ MongoDB - [mongo](https://hub.docker.com/_/mongo).
- Docker образ MinIO - [minio/minio](https://hub.docker.com/r/minio/minio).
- Docker образ Trino - [trinodb/trino](https://hub.docker.com/r/trinodb/trino).

## Назначение сервисов

- `postgres` хранит реляционную модель университета: студентов, преподавателей, курсы, записи на курсы, задания и сдачи.
- `mongodb` хранит документы обратной связи по сдачам. В каждом документе есть массив `rubric` с критериями оценивания.
- `minio` используется как S3-совместимое объектное хранилище для manifest-файла с информацией о файлах работ.
- `trino` выполняет федеративные SQL-запросы к Postgres, MongoDB и MinIO через каталоги `postgres`, `mongodb` и `minio`.

## Структура проекта

```text
lab4/
  docker-compose.yml
  postgres/init/01_schema.sql
  postgres/init/02_data.sql
  mongo/init/01_submission_feedback.js
  model4_university/minio/submission_files_manifest.csv
  model4_university/mongodb/submission_feedback.csv
  model4_university/postgres/*.csv
  minio/init/load-manifest.sh
  trino/catalog/postgres.properties
  trino/catalog/mongodb.properties
  trino/catalog/minio.properties
  sql/01_course_load.sql
  sql/02_submission_punctuality.sql
  sql/03_grade_distribution.sql
  sql/04_rubric_evaluation.sql
  sql/05_submission_files.sql
  sql/06_course_quality_mart.sql
```

## Модель данных

Postgres:

- `students(student_id, full_name, group_name, enrollment_year, email)` - студенты, учебные группы и год поступления.
- `teachers(teacher_id, full_name, department)` - преподаватели.
- `courses(course_id, teacher_id, course_name, semester)` - учебные курсы.
- `enrollments(enrollment_id, course_id, student_id, enrolled_dt)` - записи студентов на курсы.
- `assignments(assignment_id, course_id, title, due_dt, max_score)` - задания с дедлайнами.
- `submissions(submission_id, assignment_id, student_id, submitted_ts, grade)` - факты сдачи и итоговые оценки.

MongoDB:

- `university.submission_feedback` - документы с `submission_id`, комментарием преподавателя и массивом `rubric`.
- Элемент `rubric` содержит `criterion`, `points`, `max_points` и `comment`; `max_points` добавляется при загрузке как `5`.

MinIO:

- `submission_files_manifest.csv` - manifest с колонками `assignment_id`, `student_id`, `submission_id`, `file_path`, `size_kb`.
- Manifest загружается из архивного набора `model4_university`.

## Демонстрационные данные

В Postgres загружаются 140 студентов, 16 преподавателей, 28 курсов, 620 записей студентов на курсы, 70 заданий и 1562 сдачи.

В MongoDB загружаются 900 документов feedback. Массив `rubric` содержит разные критерии: `correctness`, `report`, `style`, `tests`, `performance`.

В MinIO подготовлен CSV manifest на 1562 строки с путями файлов работ и размерами в килобайтах.

## SQL-задачи

1. [01_course_load.sql](sql/01_course_load.sql) считает по каждому курсу число студентов и число заданий, затем выводит топ-5 курсов по числу студентов.
2. [02_submission_punctuality.sql](sql/02_submission_punctuality.sql) соединяет `submissions` и `assignments`, рассчитывает `delay_days` и долю просрочек по курсам и группам.
3. [03_grade_distribution.sql](sql/03_grade_distribution.sql) считает среднюю оценку, медиану, долю нулей и отмечает слишком сложные задания по низкому среднему баллу и высокой доле просрочек.
4. [04_rubric_evaluation.sql](sql/04_rubric_evaluation.sql) соединяет Postgres и MongoDB, разворачивает массив `rubric` и показывает критерии с частыми просадками.
5. [05_submission_files.sql](sql/05_submission_files.sql) читает manifest из MinIO, считает средний размер файлов по заданиям, выводит топ-10 больших работ и находит сдачи без файла.
6. [06_course_quality_mart.sql](sql/06_course_quality_mart.sql) собирает витрину качества курса со средней оценкой, долей просрочек, средним размером файла и средним баллом по `correctness`.

## Пошаговая настройка и проверка

Этот раздел можно использовать как чек-лист полного ручного запуска после клонирования проекта. Команды нужно выполнять из корня репозитория или из папки `lab4`, как указано ниже.

### 1. Подготовить окружение

Нужно установить и запустить Docker Desktop.

```powershell
# Перейти в папку практической работы.
cd lab4
```

### 2. Запустить сервисы

```powershell
# Запустить Postgres, MongoDB, MinIO и Trino в фоне.
docker compose up -d

# Проверить, что контейнеры созданы и работают.
docker compose ps
```

В списке должны быть контейнеры:

- `lab4-postgres`;
- `lab4-mongodb`;
- `lab4-minio`;
- `lab4-trino`.

Если Trino стартует дольше остальных сервисов, нужно подождать 20-40 секунд и повторить проверку:

```powershell
# Посмотреть последние строки логов Trino.
docker logs --tail 50 lab4-trino
```

### 3. Загрузить manifest в MinIO

Postgres и MongoDB загружают данные автоматически из каталогов `postgres/init` и `mongo/init`. Для MinIO нужно вручную создать бакет и положить CSV manifest.

```powershell
# Загрузить CSV manifest в MinIO через контейнер minio/mc.
docker run --rm --network lab4_trino-net --entrypoint /bin/sh -v "${PWD}/model4_university/minio:/data:ro" -v "${PWD}/minio/init:/init:ro" minio/mc /init/load-manifest.sh
```

Проверить загрузку можно через веб-консоль MinIO:

- адрес: `http://localhost:9001`;
- логин: `minio`;
- пароль: `minio123`;
- бакет: `course-data`;
- файл: `submission-files/submission_files_manifest.csv`.

### 4. Зарегистрировать таблицу MinIO в Trino

Открыть Trino CLI:

```powershell
# Открыть интерактивную консоль Trino.
docker exec -it lab4-trino trino
```

Вставить в консоль Trino SQL:

```sql
-- Удалить старую регистрацию manifest, если она была создана для прежнего датасета.
DROP TABLE IF EXISTS minio.analytics.submission_files_manifest;

-- Создать схему для внешней таблицы в Hive-каталоге.
CREATE SCHEMA IF NOT EXISTS minio.analytics
WITH (location = 's3://course-data/');

-- Зарегистрировать CSV manifest как таблицу Trino.
CREATE TABLE IF NOT EXISTS minio.analytics.submission_files_manifest (
    assignment_id varchar,
    student_id varchar,
    submission_id varchar,
    file_path varchar,
    size_kb varchar
)
WITH (
    external_location = 's3://course-data/submission-files/',
    format = 'CSV',
    skip_header_line_count = 1
);
```

В Hive-каталоге Trino для CSV все колонки объявлены как `varchar`: числовые поля приводятся к `integer` и `bigint` уже в SQL-скриптах.

Выйти из Trino CLI:

```sql
-- Закрыть интерактивную консоль.
EXIT;
```

### 5. Проверить подключение к источникам

Открыть Trino CLI снова:

```powershell
# Открыть Trino CLI для контрольных запросов.
docker exec -it lab4-trino trino
```

Выполнить проверки:

```sql
-- Проверить, что Trino видит все каталоги.
SHOW CATALOGS;

-- Проверить количество студентов в Postgres.
SELECT count(*) AS students_count
FROM postgres.public.students;

-- Проверить количество сдач в Postgres.
SELECT count(*) AS submissions_count
FROM postgres.public.submissions;

-- Проверить количество feedback-документов в MongoDB.
SELECT count(*) AS feedback_count
FROM mongodb.university.submission_feedback;

-- Проверить количество строк manifest из MinIO.
SELECT count(*) AS manifest_rows
FROM minio.analytics.submission_files_manifest;
```

Ожидаемые значения:

- `students_count` = `140`;
- `submissions_count` = `1562`;
- `feedback_count` = `900`;
- `manifest_rows` = `1562`.

### 6. Запустить SQL-скрипты

```powershell
# Выполнить запрос по нагрузке курсов.
Get-Content -Raw .\sql\01_course_load.sql | docker exec -i lab4-trino trino
"7","Course_7","28","3"
"18","Course_18","27","2"
"8","Course_8","27","1"
"5","Course_5","26","5"
"14","Course_14","26","4"

# Выполнить запрос по пунктуальности сдач.
Get-Content -Raw .\sql\02_submission_punctuality.sql | docker exec -i lab4-trino trino
"1","CS-1-A","4","0.75","0.25"
"1","CS-1-B","2","2.0","0.5"
"1","CS-1-C","2","0.0","0.0"
"1","CS-2-A","8","0.5","0.25"
"1","CS-2-B","2","0.0","0.0"
"1","CS-2-C","6","0.5","0.167"
"1","CS-3-A","2","1.0","0.5"
"1","CS-3-C","2","0.0","0.0"
"1","CS-4-A","4","2.25","0.75"
"1","CS-4-C","6","0.5","0.333"
"3","CS-1-A","2","0.0","0.0"
"3","CS-1-B","4","1.0","0.5"
"3","CS-1-C","2","1.5","0.5"
"3","CS-2-A","4","1.0","0.25"
"3","CS-2-B","2","0.0","0.0"
"3","CS-2-C","6","1.67","0.5"
"3","CS-3-A","10","1.4","0.6"
"3","CS-4-B","2","0.0","0.0"
"3","CS-4-C","10","1.2","0.4"
# ...

# Выполнить запрос по распределению оценок.
Get-Content -Raw .\sql\03_grade_distribution.sql | docker exec -i lab4-trino trino
"17","22","Assignment_22","20","6.35","7.0","0.0","0.45","false"
"9","42","Assignment_42","19","6.74","7.0","0.0","0.474","false"
"12","25","Assignment_25","20","6.8","7.0","0.0","0.4","false"
"5","41","Assignment_41","26","6.81","7.0","0.0","0.154","false"
"25","50","Assignment_50","25","6.84","7.0","0.0","0.4","false"
"18","5","Assignment_5","27","6.85","7.0","0.0","0.481","false"
"9","57","Assignment_57","19","7.11","7.0","0.0","0.474","false"
"24","32","Assignment_32","24","7.33","7.0","0.0","0.583","false"
"13","18","Assignment_18","24","7.67","8.0","0.0","0.5","false"
"19","19","Assignment_19","26","13.27","15.0","0.0","0.385","false"
"18","6","Assignment_6","27","13.41","13.0","0.0","0.259","false"
"14","16","Assignment_16","26","14.0","13.0","0.0","0.154","false"
"19","70","Assignment_70","26","14.08","14.0","0.0","0.5","false"
"26","58","Assignment_58","18","14.17","14.0","0.0","0.333","false"
# ...

# Выполнить запрос по rubric из MongoDB.
Get-Content -Raw .\sql\04_rubric_evaluation.sql | docker exec -i lab4-trino trino
"report","621","2.4","0.481","0.523"
"correctness","638","2.44","0.488","0.517"
"tests","640","2.52","0.504","0.497"
"performance","610","2.53","0.505","0.484"
"style","635","2.66","0.531","0.455"

# Выполнить запрос по файлам из MinIO.
Get-Content -Raw .\sql\05_submission_files.sql | docker exec -i lab4-trino trino
"1","19","2641.32"
"2","26","2602.38"
"3","16","3431.38"
"4","20","2157.4"
"5","27","2199.22"
"6","27","2355.74"
"7","23","1915.17"
"8","17","1888.88"
"9","17","1812.76"
"10","23","1884.74"
"11","28","2603.64"
"12","24","2233.17"
# ...
"47","3","submission_47.zip","4995.0","5114880","s3://course-data/submissions_files/assignment_id=3/student_id=139/submission_47.zip"
"1301","59","submission_1301.zip","4984.0","5103616","s3://course-data/submissions_files/assignment_id=59/student_id=54/submission_1301.zip"
"944","43","submission_944.zip","4981.0","5100544","s3://course-data/submissions_files/assignment_id=43/student_id=61/submission_944.zip"
"459","21","submission_459.zip","4978.0","5097472","s3://course-data/submissions_files/assignment_id=21/student_id=11/submission_459.zip"
"492","22","submission_492.zip","4970.0","5089280","s3://course-data/submissions_files/assignment_id=22/student_id=104/submission_492.zip"
"359","17","submission_359.zip","4969.0","5088256","s3://course-data/submissions_files/assignment_id=17/student_id=18/submission_359.zip"
"1333","61","submission_1333.zip","4969.0","5088256","s3://course-data/submissions_files/assignment_id=61/student_id=68/submission_1333.zip"
"510","23","submission_510.zip","4968.0","5087232","s3://course-data/submissions_files/assignment_id=23/student_id=111/submission_510.zip"
"616","28","submission_616.zip","4967.0","5086208","s3://course-data/submissions_files/assignment_id=28/student_id=16/submission_616.zip"
"497","23","submission_497.zip","4961.0","5080064","s3://course-data/submissions_files/assignment_id=23/student_id=32/submission_497.zip"

# Выполнить запрос витрины качества курса.
Get-Content -Raw .\sql\06_course_quality_mart.sql | docker exec -i lab4-trino trino
"1","Course_1","40.03","0.289","2847.79","1.5"
"2","Course_2","","","",""
"3","Course_3","24.95","0.405","2670.57","2.5"
"4","Course_4","","","",""
"5","Course_5","22.68","0.269","2514.15","2.28"
"6","Course_6","17.83","0.425","2606.07","2.62"
"7","Course_7","18.87","0.405","2591.32","3.07"
"8","Course_8","36.22","0.407","2829.26","2.82"
"9","Course_9","20.53","0.421","2479.95","2.28"
"10","Course_10","33.04","0.348","1884.74","2.45"
"11","Course_11","18.58","0.375","2495.13","2.33"
"12","Course_12","14.87","0.317","2424.13","2.48"
"13","Course_13","13.81","0.458","2436.9","2.83"
"14","Course_14","27.6","0.365","2801.09","2.64"
"15","Course_15","27.16","0.374","2283.1","2.5"
"16","Course_16","23.04","0.314","2106.8","2.2"
"17","Course_17","16.73","0.417","2544.55","2.37"
"18","Course_18","10.13","0.37","2277.48","1.81"
"19","Course_19","17.38","0.413","2589.58","2.63"
"20","Course_20","21.91","0.087","2321.74","3.0"
"21","Course_21","26.92","0.413","2748.3","2.04"
"22","Course_22","18.06","0.394","2659.53","2.32"
"23","Course_23","22.5","0.438","2704.92","2.93"
"24","Course_24","21.49","0.403","2260.07","2.44"
"25","Course_25","6.84","0.4","2468.88","3.22"
"26","Course_26","22.61","0.403","2536.32","2.35"
"27","Course_27","22.0","0.429","2564.95","2.64"
"28","Course_28","","","",""
```

### 7. Остановить стенд

```powershell
# Остановить контейнеры без удаления volume с данными MinIO.
docker compose down

# Полностью удалить контейнеры и volume, если нужен чистый повторный запуск.
docker compose down -v
```
