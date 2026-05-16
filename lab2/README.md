# PiROD

Лабораторная работа 2.

# Задание

## Распределенная обработка данных в Apache Spark

Реализовать стриминговый пайплайн обработки данных на Apache Spark.

Выбран усложненный вариант: данные загружаются отдельным producer-сервисом в Kafka, после чего Spark Structured Streaming читает Kafka topic, обрабатывает сообщения и записывает результат в Postgres.

```text
Red Wine Quality CSV -> Producer -> Kafka topic -> Spark Structured Streaming -> Postgres
```

# Решение

## Датасет

В качестве исходных данных используется датасет [Red Wine Quality](https://www.kaggle.com/datasets/uciml/red-wine-quality-cortez-et-al-2009). Он содержит физико-химические характеристики образцов красного вина и итоговую экспертную оценку качества `quality`.

CSV-файл располагается по пути:

```text
lab2/data/winequality-red.csv
```

Структура датасета:

| Колонка | Тип | Описание |
| --- | --- | --- |
| `fixed acidity` | float | Фиксированная кислотность вина. |
| `volatile acidity` | float | Летучая кислотность. |
| `citric acid` | float | Содержание лимонной кислоты. |
| `residual sugar` | float | Остаточный сахар. |
| `chlorides` | float | Содержание хлоридов. |
| `free sulfur dioxide` | float | Свободный диоксид серы. |
| `total sulfur dioxide` | float | Общий диоксид серы. |
| `density` | float | Плотность вина. |
| `pH` | float | Кислотно-щелочной показатель. |
| `sulphates` | float | Содержание сульфатов. |
| `alcohol` | float | Содержание алкоголя. |
| `quality` | int | Оценка качества от 0 до 10. |

В producer имена признаков приводятся к JSON-ключам в стиле `snake_case`, кроме поля `pH`, которое сохраняется как `pH` и затем в Spark переименовывается в `ph` для записи в Postgres.

## Docker-сервисы

Файл `docker-compose.yml` поднимает четыре сервиса:

| Сервис | Назначение |
| --- | --- |
| `postgres` | Хранит обработанные строки и агрегированные показатели. При старте выполняет `postgres/init.sql`. |
| `kafka` | Принимает JSON-сообщения producer и хранит topic `red-wine-quality`. |
| `producer` | Читает CSV-файл, формирует JSON и отправляет сообщения в Kafka с паузой между отправками. |
| `spark-app` | Запускает `spark-submit`, читает Kafka topic, выполняет Spark Structured Streaming pipeline и пишет данные в Postgres через JDBC. |

Для Spark в команде `spark-submit` указаны пакеты:

```text
org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1
org.postgresql:postgresql:42.7.3
```

Они нужны для чтения Kafka source и записи в Postgres через JDBC.

## Postgres

Инициализация базы описана в `postgres/init.sql`.

### Таблица `wine_events`

Таблица хранит детальные обработанные строки, которые прошли фильтры `quality >= 6` и `sulphates <= 1.0`.

Основные поля:

- физико-химические признаки вина;
- `quality` - исходная оценка качества;
- `quality_group` - группа качества, рассчитанная через UDF;
- `kafka_timestamp` - время сообщения в Kafka;
- `processed_at` - время записи micro-batch в Postgres.

### Таблица `wine_quality_stats`

Таблица хранит агрегаты по каждому Spark micro-batch и группе `quality_group`.

Поля агрегатов:

- `row_count` - количество строк в группе;
- `avg_alcohol` - среднее значение `alcohol`;
- `avg_volatile_acidity` - среднее значение `volatile_acidity`;
- `min_ph` - минимальное значение `pH`;
- `max_ph` - максимальное значение `pH`;
- `batch_id` - идентификатор micro-batch;
- `calculated_at` - время расчета агрегатов.

## Producer

Producer реализован в `producer/producer.py`.

Алгоритм работы:

1. Читает настройки из переменных окружения:
   - `CSV_PATH`;
   - `KAFKA_BOOTSTRAP_SERVERS`;
   - `KAFKA_TOPIC`;
   - `SEND_INTERVAL_SECONDS`.
2. Определяет разделитель CSV через `csv.Sniffer`. Если разделитель определить не удалось, используется `;`.
3. Читает `data/winequality-red.csv` через `csv.DictReader`.
4. Преобразует каждую строку:
   - числовые признаки приводятся к `float`;
   - `quality` приводится к `int`;
   - имена колонок приводятся к JSON-ключам.
5. Подключается к Kafka с повторными попытками, если брокер еще не готов.
6. Отправляет строки в topic `red-wine-quality`.
7. Делает паузу между сообщениями.
8. После окончания CSV снова начинает отправку с первой строки.

Dockerfile producer находится в `producer/Dockerfile`, зависимости указаны в `producer/requirements.txt`.

## Spark Pipeline

Spark-приложение находится в `spark/spark_app.py`.

Pipeline выполняется в режиме Spark Structured Streaming:

1. `readStream` читает Kafka topic `red-wine-quality`.
2. Поле `value` приводится из binary к string.
3. JSON парсится функцией `from_json` по явной схеме `StructType`.
4. Поле `pH` переименовывается в `ph`.
5. Некорректные сообщения с пустым `quality` отбрасываются.
6. Добавляется простая детекция аномалий:

```text
sulphates > 1.0
```

Такие строки выводятся в лог Spark-приложения с префиксом `[ANOMALY]` и убираются из основного потока обработки внутри `foreachBatch`.

7. Добавляется UDF `classify_quality`, которая формирует поле `quality_group`:

| Условие | Группа |
| --- | --- |
| `quality <= 4` | `low` |
| `quality <= 6` | `medium` |
| `quality >= 7` | `high` |
| `quality is null` | `unknown` |

После фильтров `sulphates <= 1.0` и `quality >= 6` в Postgres попадают группы `medium` и `high`. Группа `low` оставлена в UDF для полноты логики классификации.

8. Запись выполняется через `foreachBatch`.
9. В каждом micro-batch:
   - аномалии выводятся в лог;
   - аномалии убираются из основного потока;
   - для неаномальных строк применяется фильтр `quality >= 6`;
   - обработанные строки записываются в `wine_events`;
   - агрегаты по `quality_group` записываются в `wine_quality_stats`.

## DAG выполнения

Логический DAG обработки:

```text
Kafka source
    -> cast(value as string)
    -> from_json(value, explicit_schema)
    -> select normalized columns
    -> filter quality is not null
    -> detect anomalies by sulphates > 1.0
    -> UDF classify_quality(quality)
    -> foreachBatch
        -> log anomalies
        -> filter is_anomaly = false
        -> filter quality >= 6
        -> write wine_events via JDBC
        -> groupBy quality_group
        -> aggregate count, avg alcohol, avg volatile acidity, min pH, max pH
        -> write wine_quality_stats via JDBC
```

Описание этапов:

1. **Kafka source** - Spark читает поток сообщений из topic `red-wine-quality`.
2. **Декодирование** - binary-поле `value` преобразуется в строку JSON.
3. **Парсинг JSON** - `from_json` применяет явную схему с типами `DoubleType` и `IntegerType`.
4. **Нормализация колонок** - Spark выбирает только нужные поля и переименовывает `pH` в `ph`.
5. **Фильтрация валидности** - строки без `quality` отбрасываются.
6. **Детекция аномалий** - строки с `sulphates > 1.0` помечаются как аномальные.
7. **UDF** - функция `classify_quality` добавляет категорию качества.
8. **foreachBatch** - каждый micro-batch обрабатывается как обычный DataFrame.
9. **Логирование аномалий** - аномальные строки выводятся в лог Spark-приложения.
10. **Фильтр основного потока** - аномалии убираются, затем остаются только вина с `quality >= 6`.
11. **Запись событий** - детальные строки сохраняются в `wine_events`.
12. **Агрегация** - данные группируются по `quality_group`.
13. **Запись агрегатов** - рассчитанные показатели сохраняются в `wine_quality_stats`.
14. **Checkpoint** - Spark сохраняет состояние query в директории `SPARK_CHECKPOINT_DIR`.

## Data workflow

1. Producer читает строки из `data/winequality-red.csv`.
2. Каждая строка приводится к JSON-формату и отправляется в Kafka topic `red-wine-quality`.
3. Spark Structured Streaming читает сообщения из Kafka.
4. Spark парсит JSON по явной схеме и нормализует имена колонок.
5. Строки без `quality` отбрасываются как некорректные.
6. Для каждой валидной строки рассчитываются поля `is_anomaly` и `anomaly_reason`.
7. В `foreachBatch` строки с `sulphates > 1.0` выводятся в лог с префиксом `[ANOMALY]`.
8. Аномальные строки исключаются из основного потока обработки.
9. Для оставшихся строк применяется бизнес-фильтр `quality >= 6`.
10. Неаномальные строки записываются в таблицу `wine_events`.
11. По этим же строкам считаются агрегаты по `quality_group`.
12. Агрегаты записываются в таблицу `wine_quality_stats`.

## Структура файлов

```text
lab2/
  data/
    winequality-red.csv
  docker-compose.yml
  postgres/
    init.sql
  producer/
    Dockerfile
    producer.py
    requirements.txt
  spark/
    spark_app.py
  README.md
```

## Итог

В практической работе подготовлен стриминговый пайплайн усложненного варианта:

```text
CSV -> Python Producer -> Kafka -> Spark Structured Streaming -> Postgres
```

Producer циклично отправляет строки датасета в Kafka. Spark читает поток, парсит JSON по явной схеме, выводит в лог аномалии с `sulphates > 1.0`, убирает их из основного потока, фильтрует вина с `quality >= 6`, добавляет UDF-группу качества, считает агрегаты и записывает результат в две таблицы Postgres.

## Инструкция по настройке, запуску и проверке

### 1. Предварительные условия

Перед запуском должны быть установлены:

- Docker Desktop;
- Docker Compose;
- свободные порты `5432` и `9092`.

Работать нужно из папки `lab2`:

```powershell
cd lab2
```

Файл датасета должен находиться по пути:

```text
data/winequality-red.csv
```

Если используется полный файл с Kaggle, его нужно сохранить с тем же именем `winequality-red.csv`.

### 2. Запуск сервисов

Запустить все сервисы:

```powershell
docker compose up --build
```

После запуска должны стартовать контейнеры:

- `lab2-postgres`;
- `lab2-kafka`;
- `lab2-producer`;
- `lab2-spark-app`.

Producer начнет циклично читать CSV и отправлять JSON-сообщения в Kafka topic `red-wine-quality`. Spark-приложение начнет читать этот topic, фильтровать строки и писать результат в Postgres.

### 3. Проверка логов

Проверить, что producer отправляет сообщения:

```powershell
docker compose logs -f producer
```

В логах должны появляться строки вида:

```text
Sent record 1 to topic red-wine-quality: {...}
```

Проверить, что Spark-приложение запустило streaming query:

```powershell
docker compose logs -f spark-app
```

В логах не должно быть ошибок подключения к Kafka или Postgres. Первичная загрузка Spark-пакетов может занять время.

### 4. Проверка таблиц Postgres

Открыть psql внутри контейнера Postgres:

```powershell
docker compose exec postgres psql -U wine_user -d wine_quality
```

Проверить, что таблицы созданы:

```sql
\dt
```

Ожидаемые таблицы:

```text
wine_events
wine_quality_stats
```

Проверить количество обработанных строк:

```sql
SELECT COUNT(*) FROM wine_events;
```

Значение должно расти, потому что producer отправляет CSV циклично.

Посмотреть несколько обработанных событий:

```sql
SELECT
    event_id,
    quality,
    quality_group,
    alcohol,
    volatile_acidity,
    ph,
    processed_at
FROM wine_events
ORDER BY event_id DESC
LIMIT 10;
```

В таблице `wine_events` должны быть только строки с `quality >= 6` и `sulphates <= 1.0`.

Проверить агрегаты:

```sql
SELECT
    batch_id,
    quality_group,
    row_count,
    avg_alcohol,
    avg_volatile_acidity,
    min_ph,
    max_ph,
    calculated_at
FROM wine_quality_stats
ORDER BY stats_id DESC
LIMIT 10;
```

В таблице `wine_quality_stats` должны появляться агрегаты по `quality_group`.

### 5. Проверка Kafka topic

Посмотреть список topic:

```powershell
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list
```

В списке должен быть topic:

```text
red-wine-quality
```

Посмотреть сообщения из topic:

```powershell
docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic red-wine-quality --from-beginning --max-messages 5
```

Сообщения должны быть в JSON-формате с полями датасета:

```json
{"fixed_acidity": 7.4, "volatile_acidity": 0.7, "citric_acid": 0.0, "residual_sugar": 1.9, "chlorides": 0.076, "free_sulfur_dioxide": 11.0, "total_sulfur_dioxide": 34.0, "density": 0.9978, "pH": 3.51, "sulphates": 0.56, "alcohol": 9.4, "quality": 5}
```

### 6. Остановка сервисов

Остановить контейнеры без удаления данных Postgres и Spark checkpoint:

```powershell
docker compose down
```

Остановить контейнеры и удалить volumes:

```powershell
docker compose down -v
```

Команда с `-v` удалит данные Postgres и checkpoint Spark. После следующего запуска таблицы будут созданы заново из `postgres/init.sql`.

# Практическое задание

В [lab2](lab2) надо добавить детекцию аномалий, которая выводить их в лог и убирает аномалии из основого потока обработки. Детекция аномалий должна быть максимально простая - это может быть, например, отсечение по порогу.

# Решение

В `spark/spark_app.py` добавлена простая детекция аномалий по порогу `sulphates > 1.0`.

Для каждой строки создаются поля `is_anomaly` и `anomaly_reason`. В `foreachBatch` аномальные строки выводятся в лог Spark-приложения с префиксом `[ANOMALY]`, после чего исключаются из основного потока. В Postgres и агрегаты попадают только неаномальные строки, дополнительно прошедшие исходный фильтр `quality >= 6`.

```powershell
lab2-spark-app  | [ANOMALY] batch_id=0; data={'fixed_acidity': 7.8, 'volatile_acidity': 0.61, 'sulphates': 1.56, 'alcohol': 9.1, 'quality': 5, 'kafka_timestamp': datetime.datetime(2026, 5, 16, 9, 4, 58, 908000), 'anomaly_reason': 'sulphates > 1.0'}
lab2-spark-app  | [ANOMALY] batch_id=0; data={'fixed_acidity': 8.1, 'volatile_acidity': 0.56, 'sulphates': 1.28, 'alcohol': 9.3, 'quality': 5, 'kafka_timestamp': datetime.datetime(2026, 5, 16, 9, 5, 10, 935000), 'anomaly_reason': 'sulphates > 1.0'}
```
