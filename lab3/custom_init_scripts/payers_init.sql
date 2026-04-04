DROP EXTERNAL TABLE IF EXISTS ext_payers;

CREATE EXTERNAL TABLE ext_payers (
    id TEXT,
    name TEXT,
    address TEXT,
    city TEXT,
    state_headquartered TEXT,
    zip TEXT,
    phone TEXT
)
LOCATION ('pxf://hospitalpatientrecords/payers.csv?PROFILE=s3:text&SERVER=minio')
FORMAT 'CSV' (HEADER);
