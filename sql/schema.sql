CREATE TABLE IF NOT EXISTS fact_crime (
    crime_uid        TEXT PRIMARY KEY,
    persistent_id    TEXT,
    category         TEXT,
    month            TEXT,            -- YYYY-MM
    latitude         DOUBLE PRECISION,
    longitude        DOUBLE PRECISION,
    street_id        BIGINT,
    street_name      TEXT,
    borough          TEXT,
    outcome_category TEXT,
    outcome_date     TEXT,
    ingested_at      TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fact_crime_month    ON fact_crime (month);
CREATE INDEX IF NOT EXISTS idx_fact_crime_borough  ON fact_crime (borough);
CREATE INDEX IF NOT EXISTS idx_fact_crime_category ON fact_crime (category);

-- Marts: the aggregated views the Tableau extracts are built from

-- Crimes per borough, category and month
CREATE OR REPLACE VIEW mart_crime_by_area_month AS
SELECT
    month,
    borough,
    category,
    COUNT(*) AS crime_count
FROM fact_crime
GROUP BY month, borough, category;

-- Point-level extract for the map 
CREATE OR REPLACE VIEW mart_crime_points AS
SELECT
    month,
    borough,
    category,
    latitude,
    longitude
FROM fact_crime
WHERE latitude IS NOT NULL
  AND longitude IS NOT NULL;

-- Outcome breakdown: how crimes are resolved, by category
CREATE OR REPLACE VIEW mart_outcomes_by_category AS
SELECT
    category,
    COALESCE(outcome_category, 'Unknown / pending') AS outcome_category,
    COUNT(*) AS crime_count
FROM fact_crime
GROUP BY category, COALESCE(outcome_category, 'Unknown / pending');

-- Monthly totals for the trend line
CREATE OR REPLACE VIEW mart_monthly_totals AS
SELECT
    month,
    COUNT(*) AS crime_count
FROM fact_crime
GROUP BY month
ORDER BY month;
