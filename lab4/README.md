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
  minio/data/submission-files/submission_files_manifest.csv
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

- `students(student_id, full_name, group_name, email)` - студенты и учебные группы.
- `teachers(teacher_id, full_name, department)` - преподаватели.
- `courses(course_id, teacher_id, course_name, semester)` - учебные курсы.
- `enrollments(enrollment_id, course_id, student_id, enrolled_dt)` - записи студентов на курсы.
- `assignments(assignment_id, course_id, title, due_dt, max_score)` - задания с дедлайнами.
- `submissions(submission_id, assignment_id, student_id, submitted_ts, grade)` - факты сдачи и итоговые оценки.

MongoDB:

- `university.submission_feedback` - документы с `submission_id`, комментарием преподавателя и массивом `rubric`.
- Элемент `rubric` содержит `criterion`, `max_points` и `points`.

MinIO:

- `submission_files_manifest.csv` - manifest с колонками `submission_id`, `assignment_id`, `file_name`, `size_bytes`, `object_path`.
- В manifest намеренно отсутствуют файлы для части `submission_id`, чтобы запросы находили сдачи без файла.

## Демонстрационные данные

В Postgres загружаются 8 студентов, 3 преподавателя, 4 курса, записи студентов на курсы, 8 заданий и 29 сдач. Данные включают сдачи вовремя, просрочки, нулевые оценки и сложное задание с низкой средней оценкой.

В MongoDB загружаются документы feedback для выбранных сдач. Массив `rubric` содержит разные критерии: `correctness`, `style`, `tests`, `documentation`, `performance`. В данных есть как высокие баллы, так и частые просадки по отдельным критериям.

В MinIO подготовлен CSV manifest с файлами работ. В нем есть разные размеры файлов, несколько крупных архивов и отсутствующие записи для некоторых сдач из Postgres.

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
docker run --rm --network lab4_trino-net --entrypoint /bin/sh -v "${PWD}/minio/data:/data:ro" -v "${PWD}/minio/init:/init:ro" minio/mc /init/load-manifest.sh
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
-- Создать схему для внешней таблицы в Hive-каталоге.
CREATE SCHEMA IF NOT EXISTS minio.analytics
WITH (location = 's3://course-data/');

-- Зарегистрировать CSV manifest как таблицу Trino.
CREATE TABLE IF NOT EXISTS minio.analytics.submission_files_manifest (
    submission_id varchar,
    assignment_id varchar,
    file_name varchar,
    size_bytes varchar,
    object_path varchar
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

- `students_count` = `8`;
- `submissions_count` = `29`;
- `feedback_count` = `12`;
- `manifest_rows` = `26`.

### 6. Запустить SQL-скрипты

1. `01_course_load.sql` должен вывести топ курсов по числу студентов. Курсы `Distributed SQL`, `Databases` и `Data Pipelines` должны быть среди верхних строк.

```powershell
# Выполнить запрос по нагрузке курсов.
Get-Content -Raw .\sql\01_course_load.sql | docker exec -i lab4-trino trino
"104","Distributed SQL","6","2"
"101","Databases","5","3"
"102","Data Pipelines","5","2"
"103","Software Testing","3","1"
```

2. `02_submission_punctuality.sql` должен показать доли просрочек по `course_id` и `group_name`.
```powershell
# Выполнить запрос по пунктуальности сдач.
Get-Content -Raw .\sql\02_submission_punctuality.sql | docker exec -i lab4-trino trino
"101","CS-101","8","1.38","0.5"
"101","CS-102","5","1.4","0.6"
"102","CS-102","2","1.0","0.5"
"102","DS-201","5","1.0","0.4"
"103","CS-101","2","1.0","0.5"
"103","DS-201","1","0.0","0.0"
"104","CS-101","2","0.5","0.5"
"104","CS-102","2","1.0","0.5"
"104","DS-201","2","2.0","0.5"
```

3. `03_grade_distribution.sql` должен показать средние оценки, медианы, долю нулей и флаг `is_too_hard`.
```powershell
# Выполнить запрос по распределению оценок.
Get-Content -Raw .\sql\03_grade_distribution.sql | docker exec -i lab4-trino trino
"101","1003","Transactions lab","4","3.5","4.0","0.25","0.75","true"
"101","1001","SQL joins","5","6.0","7.0","0.2","0.4","false"
"101","1002","Indexes and plans","4","7.25","8.5","0.0","0.5","false"
"104","4002","Federated query mart","3","7.33","7.0","0.0","0.667","false"
"103","3001","Unit test suite","3","7.67","8.0","0.0","0.333","false"
"102","2001","Kafka ingestion","4","9.0","12.0","0.25","0.5","false"
"104","4001","Trino catalogs","3","10.67","11.0","0.0","0.333","false"
"102","2002","Warehouse modeling","3","12.0","13.0","0.0","0.333","false"
```

4. `04_rubric_evaluation.sql` должен вывести критерии rubric, где чаще всего есть просадки.
```powershell
# Выполнить запрос по rubric из MongoDB.
Get-Content -Raw .\sql\04_rubric_evaluation.sql | docker exec -i lab4-trino trino
"tests","5","0.9","0.35","0.8"
"correctness","12","3.38","0.496","0.583"
"documentation","7","2.11","0.632","0.429"
"style","8","1.27","0.65","0.375"
"performance","4","1.33","0.558","0.25"
```

5. `05_submission_files.sql` должен вернуть три результата: средний размер файлов по заданиям, топ-10 больших файлов и список сдач без файла (сдачи, у которых есть запись в Postgres, но нет файла в MinIO manifest).
```powershell
# Выполнить запрос по файлам из MinIO.
Get-Content -Raw .\sql\05_submission_files.sql | docker exec -i lab4-trino trino
# assignment_id, file_count, avg_file_size_kb
"1001","4","16.66"
"1002","4","335.54"
"1003","4","372.97"
"2001","4","679.01"
"2002","2","950.24"
"3001","3","237.46"
"4001","3","721.52"
"4002","2","1977.54"
# submission_id, assignment_id, file_name, size_bytes, object_path
"5027","4002","mart_pavel.zip","2300000","s3://course-data/submission-files/4002/5027/mart_pavel.zip"
"5028","4002","mart_elena.zip","1750000","s3://course-data/submission-files/4002/5028/mart_elena.zip"
"5020","2002","warehouse_dmitry.zip","1500200","s3://course-data/submission-files/2002/5020/warehouse_dmitry.zip"
"5014","2001","kafka_maria.tar.gz","1048576","s3://course-data/submission-files/2001/5014/kafka_maria.tar.gz"
"5016","2001","kafka_elena.tar.gz","934221","s3://course-data/submission-files/2001/5016/kafka_elena.tar.gz"
"5026","4001","trino_maria.zip","905500","s3://course-data/submission-files/4001/5026/trino_maria.zip"
"5015","2001","kafka_pavel.tar.gz","786432","s3://course-data/submission-files/2001/5015/kafka_pavel.tar.gz"
"5010","1003","transactions_anna.zip","734003","s3://course-data/submission-files/1003/5010/transactions_anna.zip"
"5025","4001","trino_ivan.zip","705500","s3://course-data/submission-files/4001/5025/trino_ivan.zip"
"5013","1003","transactions_pavel.zip","612440","s3://course-data/submission-files/1003/5013/transactions_pavel.zip"
# submission_id, assignment_id, student_id, submitted_ts, grade
"5004","1001","4","2026-03-05 11:30:00.000000","0.00"
"5018","2002","5","2026-03-24 10:00:00.000000","8.00"
"5029","4002","6","2026-04-09 09:00:00.000000","5.00"
```

6. `06_course_quality_mart.sql` должен собрать одну строку на курс с метриками из Postgres, MongoDB и MinIO.
```powershell
# Выполнить запрос витрины качества курса.
Get-Content -Raw .\sql\06_course_quality_mart.sql | docker exec -i lab4-trino trino
"101","Databases","5.62","0.538","241.72","2.1"
"102","Data Pipelines","10.29","0.429","769.42","4.83"
"103","Software Testing","7.67","0.333","237.46","3.0"
"104","Distributed SQL","9.0","0.5","1223.93","4.17"
```

### 7. Остановить стенд

```powershell
# Остановить контейнеры без удаления volume с данными MinIO.
docker compose down

# Полностью удалить контейнеры и volume, если нужен чистый повторный запуск.
docker compose down -v
```
