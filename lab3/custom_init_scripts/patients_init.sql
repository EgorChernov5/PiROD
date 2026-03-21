DROP EXTERNAL TABLE IF EXISTS ext_patients;

CREATE EXTERNAL TABLE ext_patients (
    id TEXT,
    birthdate DATE,
    deathdate DATE,
    prefix TEXT,
    first TEXT,
    last TEXT,
    suffix TEXT,
    maiden TEXT,
    marital TEXT,
    race TEXT,
    ethnicity TEXT,
    gender TEXT,
    birthplace TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    county TEXT,
    zip TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION
)
LOCATION ('pxf://hospitalpatientrecords/patients.csv?PROFILE=s3:text&SERVER=minio')
FORMAT 'CSV' (HEADER);