#!/bin/sh

# Настраивает подключение клиента mc к MinIO внутри docker-сети.
mc alias set local http://minio:9000 minio minio123

# Создает бакет для учебного manifest и служебного каталога Hive metastore.
mc mb --ignore-existing local/course-data

# Загружает CSV manifest с данными о файлах сдач.
mc cp /data/submission-files/submission_files_manifest.csv local/course-data/submission-files/submission_files_manifest.csv
