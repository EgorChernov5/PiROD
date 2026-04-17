DROP TABLE IF EXISTS procedures_gp;
DROP TABLE IF EXISTS encounters_gp;
DROP TABLE IF EXISTS patients_gp;
DROP TABLE IF EXISTS organizations_gp;
DROP TABLE IF EXISTS payers_gp;

CREATE TABLE patients_gp (
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
DISTRIBUTED REPLICATED;

CREATE TABLE organizations_gp (
    id TEXT,
    name TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION
)
DISTRIBUTED REPLICATED;

CREATE TABLE payers_gp (
    id TEXT,
    name TEXT,
    address TEXT,
    city TEXT,
    state_headquartered TEXT,
    zip TEXT,
    phone TEXT
)
DISTRIBUTED REPLICATED;

CREATE TABLE encounters_gp (
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
DISTRIBUTED BY (id);

CREATE TABLE procedures_gp (
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
DISTRIBUTED BY (encounter);

INSERT INTO patients_gp
SELECT *
FROM ext_patients;

INSERT INTO organizations_gp
SELECT *
FROM ext_organizations;

INSERT INTO payers_gp
SELECT *
FROM ext_payers;

INSERT INTO encounters_gp
SELECT *
FROM ext_encounters;

INSERT INTO procedures_gp
SELECT *
FROM ext_procedures;

ANALYZE patients_gp;
ANALYZE organizations_gp;
ANALYZE payers_gp;
ANALYZE encounters_gp;
ANALYZE procedures_gp;

SELECT 'patients_gp' AS table_name, COUNT(*) AS row_count FROM patients_gp
UNION ALL
SELECT 'organizations_gp' AS table_name, COUNT(*) AS row_count FROM organizations_gp
UNION ALL
SELECT 'payers_gp' AS table_name, COUNT(*) AS row_count FROM payers_gp
UNION ALL
SELECT 'encounters_gp' AS table_name, COUNT(*) AS row_count FROM encounters_gp
UNION ALL
SELECT 'procedures_gp' AS table_name, COUNT(*) AS row_count FROM procedures_gp
ORDER BY table_name;
