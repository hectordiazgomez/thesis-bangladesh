
    SELECT

        CAST(e.id AS STRING)
            AS event_id,

        LOWER(e.actor.login)
            AS pusher_login,

        e.repo.name
            AS repo,

        TIMESTAMP(e.created_at)
            AS push_time,

        SAFE_CAST(
            JSON_VALUE(
                e.payload,
                '$.push_id'
            )
            AS INT64
        )
            AS push_id,

        SAFE_CAST(
            JSON_VALUE(
                e.payload,
                '$.size'
            )
            AS INT64
        )
            AS push_size,

        SAFE_CAST(
            JSON_VALUE(
                e.payload,
                '$.distinct_size'
            )
            AS INT64
        )
            AS distinct_size,

        JSON_VALUE(
            e.payload,
            '$.before'
        )
            AS before_sha,

        JSON_VALUE(
            e.payload,
            '$.head'
        )
            AS head_sha,

        JSON_VALUE(
            e.payload,
            '$.ref'
        )
            AS ref

    FROM `githubarchive.day.2024*` e

    INNER JOIN `olah-aac6b.github_shutdown.mechanism_bd_users` u

        ON LOWER(
            e.actor.login
        ) = u.login

    WHERE

        _TABLE_SUFFIX
            BETWEEN '0701' AND '0810'

        AND e.type = 'PushEvent'
    