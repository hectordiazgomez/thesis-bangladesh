-- PENDING; not executed. BigQuery Standard SQL.
-- @logins ARRAY<STRING>: lower-case logins from r2_eligibility_candidates.csv,
-- run separately per country, retaining that country label in the export.
-- Exact observed event/action counts; does NOT claim any type is productive.
SELECT LOWER(actor.login) AS login, DATE(created_at, 'UTC') AS date,
       type AS event_type, JSON_VALUE(payload, '$.action') AS action,
       COUNT(*) AS events
FROM `githubarchive.day.2024*`
WHERE _TABLE_SUFFIX BETWEEN '0501' AND '0904'
  AND LOWER(actor.login) IN UNNEST(@logins)
GROUP BY login, date, event_type, action;
-- Join to stored productive_events by country/login/date to test candidate
-- maps. Retrieve the ORIGINAL generating SQL and excluded-user bot flags
-- to establish provenance; an observationally equivalent map is insufficient.
