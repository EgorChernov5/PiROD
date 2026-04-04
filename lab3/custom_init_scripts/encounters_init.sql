DROP EXTERNAL TABLE IF EXISTS ext_encounters;

CREATE EXTERNAL TABLE ext_encounters (
    id TEXT,
    start_ts TIMESTAMPTZ,
    stop_ts TIMESTAMPTZ,
    patient TEXT,
    organization TEXT,
    payer TEXT,
    encounterclass TEXT,
    code TEXT,
    description TEXT,
    base_encounter_cost DOUBLE PRECISION,
    total_claim_cost DOUBLE PRECISION,
    payer_coverage DOUBLE PRECISION,
    reasoncode TEXT,
    reasondescription TEXT
)
LOCATION ('pxf://hospitalpatientrecords/encounters.csv?PROFILE=s3:text&SERVER=minio')
FORMAT 'CSV' (HEADER);
