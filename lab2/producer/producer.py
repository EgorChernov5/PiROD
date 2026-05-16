import csv
import json
import os
import time
from pathlib import Path

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable


# Базовые настройки берутся из окружения контейнера.
CSV_PATH = Path(os.getenv("CSV_PATH", "/app/data/winequality-red.csv"))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "red-wine-quality")
SEND_INTERVAL_SECONDS = float(os.getenv("SEND_INTERVAL_SECONDS", "3"))


# Соответствие исходных CSV-колонок и JSON-полей.
FIELD_NAMES = {
    "fixed acidity": "fixed_acidity",
    "volatile acidity": "volatile_acidity",
    "citric acid": "citric_acid",
    "residual sugar": "residual_sugar",
    "chlorides": "chlorides",
    "free sulfur dioxide": "free_sulfur_dioxide",
    "total sulfur dioxide": "total_sulfur_dioxide",
    "density": "density",
    "pH": "pH",
    "sulphates": "sulphates",
    "alcohol": "alcohol",
    "quality": "quality",
}


class RedWineQualityProducer:
    """
    Отправляет строки датасета Red Wine Quality в Kafka.

    Attributes:
        csv_path (Path): Путь до CSV-файла. По умолчанию: /app/data/winequality-red.csv.
        bootstrap_servers (str): Адрес Kafka bootstrap servers. По умолчанию: kafka:9092.
        topic (str): Kafka topic для отправки сообщений. По умолчанию: red-wine-quality.
        interval_seconds (float): Пауза между сообщениями в секундах. По умолчанию: 3.0.

    Fallbacks:
        Если Kafka недоступна, producer повторяет подключение с паузой.
    """

    def __init__(
        self,
        csv_path: Path,
        bootstrap_servers: str,
        topic: str,
        interval_seconds: float,
    ) -> None:
        """
        Создает producer с настройками источника и Kafka.

        Parameters:
            csv_path (Path): Путь до CSV-файла.
            bootstrap_servers (str): Адрес Kafka bootstrap servers.
            topic (str): Kafka topic для отправки сообщений.
            interval_seconds (float): Пауза между сообщениями в секундах.

        Returns:
            None: Значение не возвращается.

        Fallbacks:
            Настройки передаются из окружения, поэтому отдельные значения можно заменить без изменения кода.
        """
        # Сохраняем параметры для повторного использования в цикле отправки.
        self.csv_path = csv_path
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.interval_seconds = interval_seconds

    def detect_delimiter(self) -> str:
        """
        Определяет разделитель CSV-файла по короткому фрагменту.

        Parameters:
            Нет параметров.

        Returns:
            str: Найденный разделитель CSV.

        Fallbacks:
            Если разделитель не удалось определить, используется точка с запятой.
        """
        # Читаем небольшой фрагмент файла для csv.Sniffer.
        with self.csv_path.open("r", encoding="utf-8", newline="") as csv_file:
            sample = csv_file.read(2048)

        # Возвращаем разделитель или стандартный символ исходного датасета UCI.
        try:
            return csv.Sniffer().sniff(sample, delimiters=";,").delimiter
        except csv.Error:
            return ";"

    def normalize_row(self, row: dict[str, str]) -> dict[str, object]:
        """
        Преобразует CSV-строку в JSON-совместимый словарь.

        Parameters:
            row (dict[str, str]): Строка CSV, прочитанная через DictReader.

        Returns:
            dict[str, object]: Нормализованная строка с числовыми значениями.

        Fallbacks:
            Если в строке есть неизвестные поля, они пропускаются.
        """
        normalized_row = {}

        # Приводим имена колонок к формату, ожидаемому Spark-схемой.
        for source_name, target_name in FIELD_NAMES.items():
            value = row.get(source_name)
            if value is None:
                continue

            # Для целевой переменной используем integer, остальные признаки являются float.
            if target_name == "quality":
                normalized_row[target_name] = int(float(value))
            else:
                normalized_row[target_name] = float(value)

        return normalized_row

    def load_records(self) -> list[dict[str, object]]:
        """
        Загружает все строки CSV в память producer.

        Parameters:
            Нет параметров.

        Returns:
            list[dict[str, object]]: Список строк датасета в JSON-совместимом формате.

        Fallbacks:
            Если файл пустой, возвращается пустой список.
        """
        delimiter = self.detect_delimiter()

        # Читаем CSV с явной UTF-8 кодировкой и поддержкой кавычек в заголовке.
        with self.csv_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=delimiter)
            return [self.normalize_row(row) for row in reader]

    def create_kafka_producer(self) -> KafkaProducer:
        """
        Создает KafkaProducer с JSON-сериализацией значений.

        Parameters:
            Нет параметров.

        Returns:
            KafkaProducer: Подключенный Kafka producer.

        Fallbacks:
            Ошибка подключения передается вызывающему коду для повторной попытки.
        """
        # KafkaProducer сериализует словарь в UTF-8 JSON перед отправкой.
        return KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda message: json.dumps(message).encode("utf-8"),
            key_serializer=lambda key: str(key).encode("utf-8"),
            acks="all",
            retries=5,
        )

    def wait_for_kafka(self) -> KafkaProducer:
        """
        Ожидает доступности Kafka и возвращает producer.

        Parameters:
            Нет параметров.

        Returns:
            KafkaProducer: Подключенный Kafka producer.

        Fallbacks:
            При недоступности Kafka попытка повторяется каждые 5 секунд.
        """
        # Повторяем подключение, пока Kafka не станет доступна.
        while True:
            try:
                return self.create_kafka_producer()
            except NoBrokersAvailable:
                print("Kafka is not ready yet. Waiting 5 seconds...")
                time.sleep(5)

    def send_forever(self) -> None:
        """
        Отправляет строки CSV в Kafka циклично.

        Parameters:
            Нет параметров.

        Returns:
            None: Значение не возвращается.

        Fallbacks:
            Если CSV пустой, producer завершает работу с ошибкой.
        """
        records = self.load_records()
        if not records:
            raise RuntimeError(f"CSV file has no records: {self.csv_path}")

        kafka_producer = self.wait_for_kafka()

        # Цикл бесконечно проходит по датасету и после последней строки начинает сначала.
        while True:
            for record_number, record in enumerate(records, start=1):
                kafka_producer.send(
                    self.topic,
                    key=record_number,
                    value=record,
                )
                kafka_producer.flush()
                print(f"Sent record {record_number} to topic {self.topic}: {record}")
                time.sleep(self.interval_seconds)


def main() -> None:
    """
    Запускает producer Red Wine Quality.

    Parameters:
        Нет параметров.

    Returns:
        None: Значение не возвращается.

    Fallbacks:
        Все параметры запуска можно заменить через переменные окружения.
    """
    # Создаем экземпляр producer и запускаем непрерывную отправку.
    producer = RedWineQualityProducer(
        csv_path=CSV_PATH,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        topic=KAFKA_TOPIC,
        interval_seconds=SEND_INTERVAL_SECONDS,
    )
    producer.send_forever()


# Точка входа контейнера producer.
if __name__ == "__main__":
    main()
