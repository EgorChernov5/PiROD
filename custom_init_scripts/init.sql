CREATE EXTERNAL TABLE ext_minio_data (
    Id,
    NAME,
    ADDRESS,
    CITY,
    STATE_HEADQUARTERED,
    ZIP,
    PHONE
)
LOACATION ('pxf://Hospital_Patient_Records/payers.csv?PROFILE=s3:text&SERVER=minio')
FORMAT 'CSV' (HEADER);