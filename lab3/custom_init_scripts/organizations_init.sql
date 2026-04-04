DROP EXTERNAL TABLE IF EXISTS ext_organizations;

CREATE EXTERNAL TABLE ext_organizations (
    id TEXT,
    name TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION
)
LOCATION ('pxf://hospitalpatientrecords/organizations.csv?PROFILE=s3:text&SERVER=minio')
FORMAT 'CSV' (HEADER);
