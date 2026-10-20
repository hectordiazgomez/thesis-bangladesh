
WITH base AS (

    SELECT

        u.country,

        LOWER(e.actor.login) AS login,

        DATE(e.created_at) AS date,

        e.type,

        e.repo.name AS repo,

        e.payload

    FROM `githubarchive.day.2024*` AS e

    INNER JOIN `olah-aac6b.github_shutdown.user_country` AS u

        ON LOWER(e.actor.login) = u.login

    WHERE

        _TABLE_SUFFIX BETWEEN
        '0501'
        AND
        '0904'

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
),

daily AS (

    SELECT

        country,

        login,

        date,

        -----------------------------------------------------
        -- PUSHES
        -----------------------------------------------------

        COUNTIF(
            type = 'PushEvent'
        ) AS pushes,


        -----------------------------------------------------
        -- COMMITS
        -----------------------------------------------------

        SUM(

            CASE

                WHEN type = 'PushEvent'

                THEN COALESCE(

                    SAFE_CAST(
                        JSON_VALUE(
                            payload,
                            '$.size'
                        )
                        AS INT64
                    ),

                    0
                )

                ELSE 0

            END

        ) AS commits,


        -----------------------------------------------------
        -- CHECK:
        -- PushEvent sin payload.size
        -----------------------------------------------------

        COUNTIF(

            type = 'PushEvent'

            AND JSON_VALUE(
                payload,
                '$.size'
            ) IS NULL

        ) AS pushes_missing_size,


        -----------------------------------------------------
        -- PULL REQUEST
        -----------------------------------------------------

        COUNTIF(

            type = 'PullRequestEvent'

            AND JSON_VALUE(
                payload,
                '$.action'
            ) = 'opened'

        ) AS pr_opened,


        COUNTIF(

            type = 'PullRequestEvent'

            AND JSON_VALUE(
                payload,
                '$.action'
            ) = 'closed'

        ) AS pr_closed,


        COUNTIF(

            type = 'PullRequestEvent'

            AND JSON_VALUE(
                payload,
                '$.action'
            ) = 'closed'

            AND JSON_VALUE(
                payload,
                '$.pull_request.merged'
            ) = 'true'

        ) AS pr_merged,


        -----------------------------------------------------
        -- ISSUES
        -----------------------------------------------------

        COUNTIF(

            type = 'IssuesEvent'

            AND JSON_VALUE(
                payload,
                '$.action'
            ) = 'closed'

        ) AS issues_closed,


        -----------------------------------------------------
        -- RELEASES
        -----------------------------------------------------

        COUNTIF(
            type = 'ReleaseEvent'
        ) AS releases,


        -----------------------------------------------------
        -- REVIEWS
        -----------------------------------------------------

        COUNTIF(
            type = 'PullRequestReviewEvent'
        ) AS pr_reviews,


        -----------------------------------------------------
        -- INTERACTIVE ACTIVITY
        -----------------------------------------------------

        COUNTIF(

            type IN (

                'IssueCommentEvent',

                'PullRequestReviewCommentEvent',

                'CommitCommentEvent',

                'PullRequestReviewEvent'

            )

        ) AS interactive_events,


        -----------------------------------------------------
        -- PRODUCTIVE EVENTS
        -----------------------------------------------------

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


        -----------------------------------------------------
        -- REPOSITORIOS ACTIVOS
        -----------------------------------------------------

        COUNT(
            DISTINCT repo
        ) AS repos_active


    FROM base

    GROUP BY

        country,
        login,
        date
)

SELECT

    *,

    ---------------------------------------------------------
    -- Output estilo Kreitmeir/Raschky
    ---------------------------------------------------------

    commits
    + issues_closed
    + pr_closed
    + releases
        AS output_main,


    CAST(

        (

            commits
            + issues_closed
            + pr_closed
            + releases

        ) > 0

        AS INT64

    ) AS any_output,


    CAST(

        productive_events > 0

        AS INT64

    ) AS any_productive


FROM daily

ORDER BY

    country,
    login,
    date
