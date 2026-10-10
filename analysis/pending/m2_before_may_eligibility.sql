-- PENDING, not executed. A genuinely pre-May eligibility window requires
-- missing Jan18–Apr30 data for all 15 countries, not just Bangladesh.
-- @logins ARRAY<STRING> per country's archived location list, lowercase.
SELECT LOWER(actor.login) AS login,
       COUNT(DISTINCT DATE(created_at, 'UTC')) AS any_event_active_days
FROM `githubarchive.day.2024*`
WHERE _TABLE_SUFFIX BETWEEN '0118' AND '0430'
  AND LOWER(actor.login) IN UNNEST(@logins)
GROUP BY login;
-- Apply an advisor-approved minimum-day rule and recovered bot rules, then
-- re-estimate the original May1–Jul17 fit, alongside the archived sample.
