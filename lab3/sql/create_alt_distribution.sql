DROP TABLE IF EXISTS procedures_gp_alt;
DROP TABLE IF EXISTS encounters_gp_alt;
DROP TABLE IF EXISTS patients_gp_alt;
DROP TABLE IF EXISTS organizations_gp_alt;
DROP TABLE IF EXISTS payers_gp_alt;

CREATE TABLE patients_gp_alt (
    LIKE patients_gp
)
DISTRIBUTED BY (city);

CREATE TABLE organizations_gp_alt (
    LIKE organizations_gp
)
DISTRIBUTED BY (name);

CREATE TABLE payers_gp_alt (
    LIKE payers_gp
)
DISTRIBUTED BY (name);

CREATE TABLE encounters_gp_alt (
    LIKE encounters_gp
)
DISTRIBUTED BY (patient);

CREATE TABLE procedures_gp_alt (
    LIKE procedures_gp
)
DISTRIBUTED BY (code);

INSERT INTO patients_gp_alt
SELECT * FROM patients_gp;

INSERT INTO organizations_gp_alt
SELECT * FROM organizations_gp;

INSERT INTO payers_gp_alt
SELECT * FROM payers_gp;

INSERT INTO encounters_gp_alt
SELECT * FROM encounters_gp;

INSERT INTO procedures_gp_alt
SELECT * FROM procedures_gp;

ANALYZE patients_gp_alt;
ANALYZE organizations_gp_alt;
ANALYZE payers_gp_alt;
ANALYZE encounters_gp_alt;
ANALYZE procedures_gp_alt;
