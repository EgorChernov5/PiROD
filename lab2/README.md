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

Таблица хранит детальные обработанные строки, которые прошли фильтр `quality >= 6`.

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
6. Применяется фильтр:

```text
quality >= 6
```

7. Добавляется UDF `classify_quality`, которая формирует поле `quality_group`:

| Условие | Группа |
| --- | --- |
| `quality <= 4` | `low` |
| `quality <= 6` | `medium` |
| `quality >= 7` | `high` |
| `quality is null` | `unknown` |

После фильтра `quality >= 6` в Postgres попадают группы `medium` и `high`. Группа `low` оставлена в UDF для полноты логики классификации.

8. Запись выполняется через `foreachBatch`.
9. В каждом micro-batch:
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
    -> filter quality >= 6
    -> UDF classify_quality(quality)
    -> foreachBatch
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
6. **Бизнес-фильтр** - остаются только вина с оценкой `quality >= 6`.
7. **UDF** - функция `classify_quality` добавляет категорию качества.
8. **foreachBatch** - каждый micro-batch обрабатывается как обычный DataFrame.
9. **Запись событий** - детальные строки сохраняются в `wine_events`.
10. **Агрегация** - данные группируются по `quality_group`.
11. **Запись агрегатов** - рассчитанные показатели сохраняются в `wine_quality_stats`.
12. **Checkpoint** - Spark сохраняет состояние query в директории `SPARK_CHECKPOINT_DIR`.

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

Producer циклично отправляет строки датасета в Kafka. Spark читает поток, парсит JSON по явной схеме, фильтрует вина с `quality >= 6`, добавляет UDF-группу качества, считает агрегаты и записывает результат в две таблицы Postgres.

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

В таблице `wine_events` должны быть только строки с `quality >= 6`.

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
