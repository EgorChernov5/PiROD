#!/bin/sh
set -eu

# Настраивает подключение клиента mc к MinIO внутри docker-сети.
mc alias set lab4minio http://minio:9000 minio minio123

# Создает бакет для учебного manifest и служебного каталога Hive metastore.
mc mb --ignore-existing lab4minio/course-data

# Загружает CSV manifest с данными о файлах сдач из архивного набора.
mc cp /data/submission_files_manifest.csv lab4minio/course-data/submission-files/submission_files_manifest.csv
