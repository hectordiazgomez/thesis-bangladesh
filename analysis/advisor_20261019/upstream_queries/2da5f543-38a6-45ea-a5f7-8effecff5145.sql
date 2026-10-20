
    SELECT
      DATE(e.created_at) AS event_date,
      LOWER(e.actor.login) AS login_lower,
      ANY_VALUE(s.login) AS login,
      e.repo.name AS repo_name,
      ANY_VALUE(CAST(e.repo.id AS STRING)) AS repo_id,
      e.type AS event_type,
      COUNT(*) AS event_count
    FROM `githubarchive.month.202409` e
    INNER JOIN `olah-aac6b.thesis_sector_recovery.bangladesh_preactive_sample_20000` s
      ON LOWER(e.actor.login) = s.login_lower
    WHERE DATE(e.created_at) BETWEEN DATE('2024-09-01') AND DATE('2024-09-30')
      AND e.type IN ('PushEvent', 'PullRequestEvent', 'PullRequestReviewEvent', 'PullRequestReviewCommentEvent', 'IssuesEvent', 'IssueCommentEvent', 'CommitCommentEvent', 'ReleaseEvent')
    GROUP BY event_date, login_lower, repo_name, event_type
    