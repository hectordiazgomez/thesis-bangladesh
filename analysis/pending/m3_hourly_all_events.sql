-- PENDING: exact BigQuery query for comparable country-user-hour event counts.
-- @country_users ARRAY<STRUCT<country STRING,login STRING>> frozen before use.
-- @start_date / @end_date DATE within 2024; @country_users may also hold
-- Venezuela comparison users, but no such location cohort exists locally.
SELECT u.country,LOWER(g.actor.login) AS login,
       TIMESTAMP_TRUNC(g.created_at,HOUR,'UTC') AS hour_UTC,
       g.type AS event_type,JSON_VALUE(g.payload,'$.action') AS action,
       COUNT(DISTINCT g.id) AS events
FROM `githubarchive.day.2024*` AS g
JOIN UNNEST(@country_users) AS u ON LOWER(g.actor.login)=LOWER(u.login)
WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%m%d',@start_date)
                        AND FORMAT_DATE('%m%d',@end_date)
GROUP BY country,login,hour_UTC,event_type,action;
-- Fill absent hours with zero after aggregating on the complete frozen cohort.
-- Primary productive_event mapping must first be recovered under R2.
-- For Rajasthan Sep26 2021, use githubarchive.day.2021* and a verified subnational
-- cohort; merely assigning all India to Rajasthan would be an invalid substitute.
