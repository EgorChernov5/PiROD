\pset pager off

\echo 'Q1 optimized'
EXPLAIN
SELECT
    e.encounterclass,
    p.description,
    COUNT(*) AS procedure_cnt
FROM encounters_gp e
JOIN procedures_gp p
    ON p.encounter = e.id
JOIN patients_gp pt
    ON pt.id = e.patient
JOIN payers_gp py
    ON py.id = e.payer
GROUP BY e.encounterclass, p.description
ORDER BY procedure_cnt DESC
LIMIT 10;

\echo 'Q1 alternative'
EXPLAIN
SELECT
    e.encounterclass,
    p.description,
    COUNT(*) AS procedure_cnt
FROM encounters_gp_alt e
JOIN procedures_gp_alt p
    ON p.encounter = e.id
JOIN patients_gp_alt pt
    ON pt.id = e.patient
JOIN payers_gp_alt py
    ON py.id = e.payer
GROUP BY e.encounterclass, p.description
ORDER BY procedure_cnt DESC
LIMIT 10;

\echo 'Q2 optimized'
EXPLAIN
SELECT
    pt.city,
    pt.state,
    py.name,
    COUNT(*) AS encounter_cnt,
    ROUND(AVG(e.total_claim_cost)::numeric, 2) AS avg_claim
FROM encounters_gp e
JOIN patients_gp pt
    ON pt.id = e.patient
JOIN payers_gp py
    ON py.id = e.payer
JOIN organizations_gp o
    ON o.id = e.organization
GROUP BY pt.city, pt.state, py.name
ORDER BY encounter_cnt DESC
LIMIT 10;

\echo 'Q2 alternative'
EXPLAIN
SELECT
    pt.city,
    pt.state,
    py.name,
    COUNT(*) AS encounter_cnt,
    ROUND(AVG(e.total_claim_cost)::numeric, 2) AS avg_claim
FROM encounters_gp_alt e
JOIN patients_gp_alt pt
    ON pt.id = e.patient
JOIN payers_gp_alt py
    ON py.id = e.payer
JOIN organizations_gp_alt o
    ON o.id = e.organization
GROUP BY pt.city, pt.state, py.name
ORDER BY encounter_cnt DESC
LIMIT 10;

\echo 'Q3 optimized'
EXPLAIN
SELECT
    o.name AS organization_name,
    py.name AS payer_name,
    e.encounterclass,
    COUNT(DISTINCT e.id) AS encounter_cnt,
    ROUND(SUM(p.base_cost)::numeric, 2) AS proc_cost
FROM procedures_gp p
JOIN encounters_gp e
    ON e.id = p.encounter
JOIN organizations_gp o
    ON o.id = e.organization
JOIN payers_gp py
    ON py.id = e.payer
GROUP BY o.name, py.name, e.encounterclass
ORDER BY proc_cost DESC
LIMIT 10;

\echo 'Q3 alternative'
EXPLAIN
SELECT
    o.name AS organization_name,
    py.name AS payer_name,
    e.encounterclass,
    COUNT(DISTINCT e.id) AS encounter_cnt,
    ROUND(SUM(p.base_cost)::numeric, 2) AS proc_cost
FROM procedures_gp_alt p
JOIN encounters_gp_alt e
    ON e.id = p.encounter
JOIN organizations_gp_alt o
    ON o.id = e.organization
JOIN payers_gp_alt py
    ON py.id = e.payer
GROUP BY o.name, py.name, e.encounterclass
ORDER BY proc_cost DESC
LIMIT 10;
