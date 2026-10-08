-- PENDING. Requires a frozen, globally enumerated country-location user list
-- @country_users ARRAY<STRUCT<country STRING, login STRING>> (currently absent).
-- Intended eligibility window is Jan18-Apr30, before the main fitting period.
WITH users AS (
 SELECT DISTINCT country, LOWER(login) AS login FROM UNNEST(@country_users)
), account_days AS (
 SELECT u.country,u.login,COUNT(DISTINCT DATE(g.created_at,'UTC')) AS active_days
 FROM `githubarchive.day.2024*` AS g JOIN users AS u ON LOWER(g.actor.login)=u.login
 WHERE _TABLE_SUFFIX BETWEEN '0118' AND '0430'
 GROUP BY u.country,u.login
)
SELECT country,COUNTIF(active_days>=4) AS eligible_before_bot_screen
FROM account_days GROUP BY country
HAVING eligible_before_bot_screen>=1000 ORDER BY country;
-- Then apply a documented bot rule and independently frozen connectivity
-- exclusions. Do not infer eligibility or absence of outages from missing data.
