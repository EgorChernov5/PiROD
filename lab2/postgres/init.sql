CREATE TABLE IF NOT EXISTS wine_events (
    event_id BIGSERIAL PRIMARY KEY,
    fixed_acidity DOUBLE PRECISION NOT NULL,
    volatile_acidity DOUBLE PRECISION NOT NULL,
    citric_acid DOUBLE PRECISION NOT NULL,
    residual_sugar DOUBLE PRECISION NOT NULL,
    chlorides DOUBLE PRECISION NOT NULL,
    free_sulfur_dioxide DOUBLE PRECISION NOT NULL,
    total_sulfur_dioxide DOUBLE PRECISION NOT NULL,
    density DOUBLE PRECISION NOT NULL,
    ph DOUBLE PRECISION NOT NULL,
    sulphates DOUBLE PRECISION NOT NULL,
    alcohol DOUBLE PRECISION NOT NULL,
    quality INTEGER NOT NULL,
    quality_group VARCHAR(20) NOT NULL,
    kafka_timestamp TIMESTAMP,
    processed_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS wine_quality_stats (
    stats_id BIGSERIAL PRIMARY KEY,
    batch_id BIGINT NOT NULL,
    quality_group VARCHAR(20) NOT NULL,
    row_count BIGINT NOT NULL,
    avg_alcohol DOUBLE PRECISION NOT NULL,
    avg_volatile_acidity DOUBLE PRECISION NOT NULL,
    min_ph DOUBLE PRECISION NOT NULL,
    max_ph DOUBLE PRECISION NOT NULL,
    calculated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_wine_events_quality_group
    ON wine_events (quality_group);

CREATE INDEX IF NOT EXISTS idx_wine_quality_stats_batch
    ON wine_quality_stats (batch_id, quality_group);
