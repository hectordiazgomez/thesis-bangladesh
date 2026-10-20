
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
                '$.size'
            )
            AS INT64
        )
            AS push_size,

        JSON_VALUE(
            c,
            '$.sha'
        )
            AS sha,

        SAFE_CAST(
            JSON_VALUE(
                c,
                '$.distinct'
            )
            AS BOOL
        )
            AS distinct_commit

    FROM `githubarchive.day.2024*` e

    INNER JOIN `olah-aac6b.github_shutdown.mechanism_bd_users` u

        ON LOWER(
            e.actor.login
        ) = u.login

    CROSS JOIN UNNEST(

        IFNULL(

            JSON_EXTRACT_ARRAY(
                e.payload,
                '$.commits'
            ),

            ARRAY<STRING>[]

        )

    ) AS c

    WHERE

        _TABLE_SUFFIX
            BETWEEN '0701' AND '0810'

        AND e.type = 'PushEvent'
    