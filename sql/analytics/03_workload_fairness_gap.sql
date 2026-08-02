-- Analytics: workload distribution gap across governed cohorts, feeding the
-- Workforce Fairness dashboard page. Small cohorts already suppressed upstream
-- in gold.mart_fairness_workload (HAVING count(*) >= 8).
WITH per_cohort AS (
    SELECT gender, avg(total_actual_hours / nullif(shift_count,0)) AS avg_hours_per_shift
    FROM gold.mart_fairness_workload
    GROUP BY 1
)
SELECT
    max(avg_hours_per_shift) - min(avg_hours_per_shift) AS max_gender_gap_hours_per_shift,
    100.0 * (max(avg_hours_per_shift) - min(avg_hours_per_shift)) / nullif(min(avg_hours_per_shift),0) AS gap_pct
FROM per_cohort;
