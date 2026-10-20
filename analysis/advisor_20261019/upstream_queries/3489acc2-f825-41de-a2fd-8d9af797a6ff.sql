
    SELECT
      DATE(e.created_at) AS event_date,
      LOWER(e.actor.login) AS login_lower,
      ANY_VALUE(u.login) AS login,
      e.repo.name AS repo_name,
      e.type AS event_type,
      COUNT(*) AS event_count
    FROM `githubarchive.month.202406` e
    INNER JOIN `olah-aac6b.thesis_sector_recovery.bangladesh_universe_87845` u
      ON LOWER(e.actor.login) = u.login_lower
    WHERE DATE(e.created_at) BETWEEN DATE('2024-06-01') AND DATE('2024-06-30')
      AND e.type IN ('PushEvent', 'PullRequestEvent', 'PullRequestReviewEvent', 'PullRequestReviewCommentEvent', 'IssuesEvent', 'IssueCommentEvent', 'CommitCommentEvent', 'ReleaseEvent')
    GROUP BY event_date, login_lower, repo_name, event_type
    