DROP EXTERNAL TABLE IF EXISTS ext_procedures;

CREATE EXTERNAL TABLE ext_procedures (
    start_ts TIMESTAMPTZ,
    stop_ts TIMESTAMPTZ,
    patient TEXT,
    encounter TEXT,
    code TEXT,
    description TEXT,
    base_cost DOUBLE PRECISION,
    reasoncode TEXT,
    reasondescription TEXT
)
LOCATION ('pxf://hospitalpatientrecords/procedures.csv?PROFILE=s3:text&SERVER=minio')
FORMAT 'CSV' (HEADER);
