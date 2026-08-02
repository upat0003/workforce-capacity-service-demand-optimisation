-- Analytics: overtime concentration by region and role, used for the Capacity and
-- Utilisation dashboard page and the overtime-reduction business case tracking.
SELECT
    location_id,
    primary_role,
    sum(total_overtime_hours) AS total_overtime_hours,
    sum(total_hours_worked) AS total_hours_worked,
    round(100.0 * sum(total_overtime_hours) / nullif(sum(total_hours_worked), 0), 2) AS overtime_pct
FROM gold.mart_weekly_overtime
GROUP BY 1,2
ORDER BY overtime_pct DESC;
