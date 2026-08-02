-- Gold: calendar dimension spanning the synthetic history plus a 90-day forecast horizon.

CREATE OR REPLACE TABLE gold.dim_date AS
WITH bounds AS (
    SELECT min(requested_date) AS min_d, max(requested_date) + INTERVAL 90 DAY AS max_d
    FROM silver.fact_service_requests
)
SELECT
    d::DATE AS date_key,
    dayname(d) AS day_name,
    dayofweek(d) AS day_of_week_num,
    CASE WHEN dayofweek(d) IN (0,6) THEN true ELSE false END AS is_weekend,
    weekofyear(d) AS iso_week,
    month(d) AS month_num,
    monthname(d) AS month_name,
    quarter(d) AS quarter_num,
    year(d) AS year_num,
    date_trunc('week', d)::DATE AS week_start_date,
    date_trunc('month', d)::DATE AS month_start_date
FROM bounds, generate_series(min_d, max_d, INTERVAL 1 DAY) AS t(d);
