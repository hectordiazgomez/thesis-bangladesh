
WITH events AS (

    SELECT

        LOWER(e.actor.login) AS login,

        DATE(TIMESTAMP(e.created_at)) AS date,

        e.type AS event_type,

        JSON_VALUE(
            e.payload,
            '$.action'
        ) AS action

    FROM `githubarchive.day.2024*` e

    INNER JOIN `olah-aac6b.github_shutdown.eligible_users_international` u

        ON LOWER(e.actor.login) = u.login

    WHERE

        _TABLE_SUFFIX
            BETWEEN '0501' AND '0904'

        AND e.type IN (
            'IssuesEvent',
            'IssueCommentEvent',
            'PullRequestReviewCommentEvent',
            'CommitCommentEvent'
        )
),

agg AS (

    SELECT

        login,
        date,

        COUNTIF(
            event_type = 'IssuesEvent'
            AND action = 'opened'
        ) AS issues_opened,

        COUNTIF(
            event_type = 'IssueCommentEvent'
        ) AS issue_comments,

        COUNTIF(
            event_type = 'PullRequestReviewCommentEvent'
        ) AS pr_review_comments,

        COUNTIF(
            event_type = 'CommitCommentEvent'
        ) AS commit_comments

    FROM events

    GROUP BY
        login,
        date
)

SELECT

    u.country,
    a.login,
    a.date,

    a.issues_opened,
    a.issue_comments,
    a.pr_review_comments,
    a.commit_comments

FROM agg a

INNER JOIN `olah-aac6b.github_shutdown.eligible_users_international` u
    ON a.login = u.login
