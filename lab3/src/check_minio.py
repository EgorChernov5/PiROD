import boto3

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    config=boto3.session.Config(signature_version='s3v4')
)

try:
    # Список бакетов
    print("📦 Бакеты:")
    for b in s3.list_buckets()['Buckets']:
        print(f"  - {b['Name']}")
    
    # Проверка конкретного бакета
    bucket = 'hospitalpatientrecords'
    print(f"\n🔍 Проверка бакета '{bucket}':")
    
    objects = s3.list_objects_v2(Bucket=bucket)
    if 'Contents' in objects:
        print(f"  ✅ Файлов: {len(objects['Contents'])}")
        for obj in objects['Contents']:
            print(f"    - {obj['Key']} ({obj['Size']} bytes)")
    else:
        print(f"  ❌ Бакет пуст или не существует")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
