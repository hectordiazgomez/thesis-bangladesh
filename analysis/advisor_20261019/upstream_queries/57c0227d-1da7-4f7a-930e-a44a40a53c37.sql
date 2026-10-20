
WITH base AS (

    SELECT
        u.country,
        LOWER(e.actor.login) AS login,
        DATE(e.created_at) AS date,
        e.type,
        e.repo.name AS repo,
        e.payload

    FROM `githubarchive.day.2024*` e

    INNER JOIN `olah-aac6b.github_shutdown.international_user_country` u
        ON LOWER(e.actor.login) = u.login

    WHERE
        _TABLE_SUFFIX BETWEEN '0501' AND '0904'

        AND e.type IN (
            'PushEvent',
            'PullRequestEvent',
            'PullRequestReviewEvent',
            'PullRequestReviewCommentEvent',
            'IssuesEvent',
            'IssueCommentEvent',
            'CommitCommentEvent',
            'ReleaseEvent',
            'CreateEvent'
        )
)

SELECT
    country,
    login,
    date,

    COUNTIF(
        type = 'PushEvent'
    ) AS pushes,

    SUM(
        CASE
            WHEN type = 'PushEvent'
            THEN COALESCE(
                SAFE_CAST(
                    JSON_VALUE(payload, '$.size')
                    AS INT64
                ),
                0
            )
            ELSE 0
        END
    ) AS commits,

    COUNTIF(
        type = 'PullRequestEvent'
        AND JSON_VALUE(payload, '$.action') = 'opened'
    ) AS pr_opened,

    COUNTIF(
        type = 'PullRequestEvent'
        AND JSON_VALUE(payload, '$.action') = 'closed'
    ) AS pr_closed,

    COUNTIF(
        type = 'PullRequestEvent'
        AND JSON_VALUE(payload, '$.action') = 'closed'
        AND JSON_VALUE(
            payload,
            '$.pull_request.merged'
        ) = 'true'
    ) AS pr_merged,

    COUNTIF(
        type = 'IssuesEvent'
        AND JSON_VALUE(payload, '$.action') = 'closed'
    ) AS issues_closed,

    COUNTIF(
        type = 'ReleaseEvent'
    ) AS releases,

    COUNTIF(
        type = 'PullRequestReviewEvent'
    ) AS pr_reviews,

    COUNTIF(
        type IN (
            'IssueCommentEvent',
            'PullRequestReviewCommentEvent',
            'CommitCommentEvent',
            'PullRequestReviewEvent'
        )
    ) AS interactive_events,

    COUNTIF(
        type IN (
            'PushEvent',
            'PullRequestEvent',
            'PullRequestReviewEvent',
            'PullRequestReviewCommentEvent',
            'IssuesEvent',
            'ReleaseEvent',
            'CreateEvent'
        )
    ) AS productive_events,

    COUNT(DISTINCT repo) AS repos_active

FROM base

GROUP BY
    country,
    login,
    date
