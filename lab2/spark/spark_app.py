import os

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T


# Настройки Kafka, Postgres и checkpoint берутся из docker-compose окружения.
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "red-wine-quality")
POSTGRES_URL = os.getenv("POSTGRES_URL", "jdbc:postgresql://postgres:5432/wine_quality")
POSTGRES_USER = os.getenv("POSTGRES_USER", "wine_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "wine_password")
SPARK_CHECKPOINT_DIR = os.getenv(
    "SPARK_CHECKPOINT_DIR",
    "/tmp/spark-checkpoints/red-wine-quality",
)


# Колонки обработанных событий соответствуют таблице wine_events.
EVENT_COLUMNS = [
    "fixed_acidity",
    "volatile_acidity",
    "citric_acid",
    "residual_sugar",
    "chlorides",
    "free_sulfur_dioxide",
    "total_sulfur_dioxide",
    "density",
    "ph",
    "sulphates",
    "alcohol",
    "quality",
    "quality_group",
    "kafka_timestamp",
    "processed_at",
]


# Порог сульфатов используется для простой детекции аномалий.
ANOMALY_SULPHATES_THRESHOLD = 1.0


# Колонки аномалий выводятся в лог Spark driver.
ANOMALY_LOG_COLUMNS = [
    "fixed_acidity",
    "volatile_acidity",
    "sulphates",
    "alcohol",
    "quality",
    "kafka_timestamp",
    "anomaly_reason",
]


def build_spark_session() -> SparkSession:
    """
    Создает SparkSession для Structured Streaming приложения.

    Parameters:
        Нет параметров.

    Returns:
        SparkSession: Настроенная Spark-сессия.

    Fallbacks:
        Пакеты Kafka и PostgreSQL передаются через spark-submit в docker-compose.
    """
    # SparkSession используется для чтения Kafka stream и записи JDBC.
    return (
        SparkSession.builder.appName("red-wine-quality-streaming")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )


def get_wine_schema() -> T.StructType:
    """
    Возвращает явную схему JSON-сообщений из Kafka.

    Parameters:
        Нет параметров.

    Returns:
        StructType: Spark-схема для Red Wine Quality.

    Fallbacks:
        Если сообщение не соответствует схеме, from_json вернет null-поля.
    """
    # Схема повторяет признаки датасета и целевую колонку quality.
    return T.StructType(
        [
            T.StructField("fixed_acidity", T.DoubleType(), True),
            T.StructField("volatile_acidity", T.DoubleType(), True),
            T.StructField("citric_acid", T.DoubleType(), True),
            T.StructField("residual_sugar", T.DoubleType(), True),
            T.StructField("chlorides", T.DoubleType(), True),
            T.StructField("free_sulfur_dioxide", T.DoubleType(), True),
            T.StructField("total_sulfur_dioxide", T.DoubleType(), True),
            T.StructField("density", T.DoubleType(), True),
            T.StructField("pH", T.DoubleType(), True),
            T.StructField("sulphates", T.DoubleType(), True),
            T.StructField("alcohol", T.DoubleType(), True),
            T.StructField("quality", T.IntegerType(), True),
        ]
    )


def get_jdbc_properties() -> dict:
    """
    Возвращает параметры подключения JDBC к Postgres.

    Parameters:
        Нет параметров.

    Returns:
        dict[str, str]: JDBC-свойства подключения.

    Fallbacks:
        Значения можно заменить через переменные окружения контейнера.
    """
    # Driver явно указывается для корректной записи через Spark JDBC.
    return {
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
        "driver": "org.postgresql.Driver",
    }


def classify_quality(quality: int) -> str:
    """
    Определяет группу качества вина по оценке quality.

    Parameters:
        quality (int): Оценка качества вина от 0 до 10.

    Returns:
        str: Название группы качества.

    Fallbacks:
        Если quality не задан, возвращается unknown.
    """
    # Разбиваем оценки на понятные группы качества.
    if quality is None:
        return "unknown"
    if quality <= 4:
        return "low"
    if quality <= 6:
        return "medium"
    return "high"


def read_kafka_stream(spark: SparkSession) -> DataFrame:
    """
    Создает streaming DataFrame из Kafka topic.

    Parameters:
        spark (SparkSession): Активная Spark-сессия.

    Returns:
        DataFrame: Поток Kafka-сообщений.

    Fallbacks:
        При потере offsets используется failOnDataLoss=false.
    """
    # Kafka source читает JSON-сообщения из topic red-wine-quality.
    return (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )


def add_anomaly_flags(wine_stream: DataFrame) -> DataFrame:
    """
    Добавляет флаги простой детекции аномалий по порогу sulphates.

    Parameters:
        wine_stream (DataFrame): Поток строк Red Wine Quality.

    Returns:
        DataFrame: Поток с колонками is_anomaly и anomaly_reason.

    Fallbacks:
        Если sulphates не задан, строка не считается аномальной.
    """
    # Считаем аномалией только превышение простого порога sulphates.
    anomaly_condition = F.coalesce(
        F.col("sulphates") > F.lit(ANOMALY_SULPHATES_THRESHOLD),
        F.lit(False),
    )

    # Добавляем флаг и понятную причину для вывода в лог.
    return wine_stream.withColumn("is_anomaly", anomaly_condition).withColumn(
        "anomaly_reason",
        F.when(
            F.col("is_anomaly"),
            F.lit(f"sulphates > {ANOMALY_SULPHATES_THRESHOLD}"),
        ).otherwise(F.lit(None).cast("string")),
    )


def parse_wine_messages(kafka_stream: DataFrame) -> DataFrame:
    """
    Парсит Kafka value как JSON и применяет бизнес-преобразования.

    Parameters:
        kafka_stream (DataFrame): Поток Kafka-сообщений.

    Returns:
        DataFrame: Поток обработанных строк Red Wine Quality.

    Fallbacks:
        Некорректные сообщения отбрасываются фильтрацией по quality.
    """
    wine_schema = get_wine_schema()
    quality_group_udf = F.udf(classify_quality, T.StringType())

    # Декодируем binary value в string и разбираем JSON по явной схеме.
    parsed_stream = kafka_stream.select(
        F.from_json(F.col("value").cast("string"), wine_schema).alias("wine"),
        F.col("timestamp").alias("kafka_timestamp"),
    )

    # Разворачиваем структуру и приводим pH к безопасному имени колонки Postgres.
    wine_stream = parsed_stream.select(
        F.col("wine.fixed_acidity").alias("fixed_acidity"),
        F.col("wine.volatile_acidity").alias("volatile_acidity"),
        F.col("wine.citric_acid").alias("citric_acid"),
        F.col("wine.residual_sugar").alias("residual_sugar"),
        F.col("wine.chlorides").alias("chlorides"),
        F.col("wine.free_sulfur_dioxide").alias("free_sulfur_dioxide"),
        F.col("wine.total_sulfur_dioxide").alias("total_sulfur_dioxide"),
        F.col("wine.density").alias("density"),
        F.col("wine.pH").alias("ph"),
        F.col("wine.sulphates").alias("sulphates"),
        F.col("wine.alcohol").alias("alcohol"),
        F.col("wine.quality").alias("quality"),
        F.col("kafka_timestamp"),
    )

    # Оставляем валидные вина, добавляем UDF-группу и флаги аномалий.
    return (
        wine_stream.filter(F.col("quality").isNotNull())
        .transform(add_anomaly_flags)
        .withColumn("quality_group", quality_group_udf(F.col("quality")))
    )


def write_jdbc_table(dataframe: DataFrame, table_name: str, mode: str = "append") -> None:
    """
    Записывает DataFrame в таблицу Postgres через JDBC.

    Parameters:
        dataframe (DataFrame): Данные для записи.
        table_name (str): Название целевой таблицы.
        mode (str): Режим записи Spark JDBC. По умолчанию: append.

    Returns:
        None: Значение не возвращается.

    Fallbacks:
        Параметры подключения берутся из окружения контейнера.
    """
    # Spark JDBC writer добавляет строки в существующие таблицы Postgres.
    (
        dataframe.write.mode(mode)
        .jdbc(
            url=POSTGRES_URL,
            table=table_name,
            properties=get_jdbc_properties(),
        )
    )


def log_anomalies(batch_df: DataFrame, batch_id: int) -> None:
    """
    Выводит найденные аномалии micro-batch в лог Spark driver.

    Parameters:
        batch_df (DataFrame): Строки текущего micro-batch.
        batch_id (int): Идентификатор micro-batch.

    Returns:
        None: Значение не возвращается.

    Fallbacks:
        Если аномалий нет, лог не выводится.
    """
    # Выбираем только аномальные строки для вывода в docker logs spark-app.
    anomaly_rows = (
        batch_df.filter(F.col("is_anomaly"))
        .select(*ANOMALY_LOG_COLUMNS)
        .collect()
    )

    # Каждая аномальная строка логируется отдельно с batch_id.
    for anomaly_row in anomaly_rows:
        print(
            f"[ANOMALY] batch_id={batch_id}; data={anomaly_row.asDict()}",
            flush=True,
        )


def build_stats(batch_df: DataFrame, batch_id: int) -> DataFrame:
    """
    Строит агрегаты качества для одного streaming micro-batch.

    Parameters:
        batch_df (DataFrame): Обработанные строки текущего micro-batch.
        batch_id (int): Идентификатор micro-batch.

    Returns:
        DataFrame: Агрегаты по quality_group.

    Fallbacks:
        Если batch пустой, функция вызывается только после внешней проверки.
    """
    # Считаем требуемые агрегаты по группе качества.
    stats_df = batch_df.groupBy("quality_group").agg(
        F.count("*").alias("row_count"),
        F.avg("alcohol").alias("avg_alcohol"),
        F.avg("volatile_acidity").alias("avg_volatile_acidity"),
        F.min("ph").alias("min_ph"),
        F.max("ph").alias("max_ph"),
    )

    # Добавляем batch_id и timestamp расчета для аудита агрегатов.
    return stats_df.withColumn("batch_id", F.lit(batch_id).cast("long")).withColumn(
        "calculated_at",
        F.current_timestamp(),
    ).select(
        "batch_id",
        "quality_group",
        "row_count",
        "avg_alcohol",
        "avg_volatile_acidity",
        "min_ph",
        "max_ph",
        "calculated_at",
    )


def write_batch_to_postgres(batch_df: DataFrame, batch_id: int) -> None:
    """
    Записывает обработанные события и агрегаты micro-batch в Postgres.

    Parameters:
        batch_df (DataFrame): Обработанные строки текущего micro-batch.
        batch_id (int): Идентификатор micro-batch.

    Returns:
        None: Значение не возвращается.

    Fallbacks:
        Пустой micro-batch пропускается без записи.
    """
    # Пустые micro-batch не записываются в Postgres.
    if batch_df.rdd.isEmpty():
        return

    # Кэшируем batch, потому что он используется для логирования и JDBC-записей.
    cached_batch = batch_df.cache()

    # Выводим аномалии в лог и убираем их из основного потока обработки.
    log_anomalies(cached_batch, batch_id)
    processed_batch = cached_batch.filter(~F.col("is_anomaly")).filter(
        F.col("quality") >= 6
    )
    if processed_batch.rdd.isEmpty():
        cached_batch.unpersist()
        return

    # Пишем детальные обработанные строки в wine_events.
    events_df = processed_batch.withColumn("processed_at", F.current_timestamp()).select(
        *EVENT_COLUMNS
    )
    write_jdbc_table(events_df, "wine_events")

    # Пишем агрегаты по quality_group в wine_quality_stats.
    stats_df = build_stats(processed_batch, batch_id)
    write_jdbc_table(stats_df, "wine_quality_stats")

    # Освобождаем память executors после завершения записи batch.
    cached_batch.unpersist()


def start_stream(processed_stream: DataFrame) -> None:
    """
    Запускает Structured Streaming query с foreachBatch.

    Parameters:
        processed_stream (DataFrame): Поток обработанных строк.

    Returns:
        None: Значение не возвращается.

    Fallbacks:
        Checkpoint directory сохраняет прогресс query между перезапусками.
    """
    # foreachBatch позволяет записать и события, и агрегаты в Postgres.
    query = (
        processed_stream.writeStream.foreachBatch(write_batch_to_postgres)
        .option("checkpointLocation", SPARK_CHECKPOINT_DIR)
        .outputMode("append")
        .start()
    )
    query.awaitTermination()


def main() -> None:
    """
    Запускает Spark Structured Streaming pipeline.

    Parameters:
        Нет параметров.

    Returns:
        None: Значение не возвращается.

    Fallbacks:
        Все подключения настраиваются через переменные окружения docker-compose.
    """
    # Собираем DAG: Kafka source -> JSON parse -> anomaly detect -> UDF -> JDBC.
    spark = build_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    kafka_stream = read_kafka_stream(spark)
    processed_stream = parse_wine_messages(kafka_stream)
    start_stream(processed_stream)


# Точка входа Spark-приложения.
if __name__ == "__main__":
    main()
