WITH snapshot AS (
    SELECT %s::date AS snapshot_date
),

params AS (
    SELECT
        snapshot_date,
        snapshot_date - INTERVAL '60 days' AS history_start,
        snapshot_date + INTERVAL '30 days' AS target_end
    FROM snapshot
),

session_stats AS (
    SELECT
        u.user_id,
        COUNT(s.session_id) AS sessions_last_60d,
        ROUND(
            AVG(s.duration_seconds)::numeric, 2
        ) AS avg_session_duration_60d
    FROM users AS u
    CROSS JOIN params AS p
    LEFT JOIN sessions AS s
        ON u.user_id = s.user_id
        AND s.started_at >= p.history_start
        AND s.started_at < p.snapshot_date
    GROUP BY u.user_id
),


order_stats AS (
    SELECT
        u.user_id,
        u.country,

        COUNT(o.order_id) FILTER (
            WHERE o.created_at < p.snapshot_date
        ) AS orders_last_60d,

        CASE
            WHEN COUNT(o.order_id) FILTER (
                WHERE o.created_at >= p.snapshot_date
                  AND o.status = 'completed'
            ) > 0 THEN 1
            ELSE 0
        END AS target

    FROM users AS u
    CROSS JOIN params AS p
    LEFT JOIN orders AS o
        ON u.user_id = o.user_id
        AND o.created_at >= p.history_start
        AND o.created_at < p.target_end

    GROUP BY u.user_id, u.country
),


event_stats AS (
    SELECT
        u.user_id,

        COUNT(e.user_id) AS events_last_60d,

        COUNT(e.user_id) FILTER (
            WHERE e.event_type = 'page_view'
        ) AS page_views_60d,

        COUNT(e.user_id) FILTER (
            WHERE e.event_type = 'product_view'
        ) AS product_views_60d,

        COUNT(e.user_id) FILTER (
            WHERE e.event_type = 'search'
        ) AS searches_60d,

        COUNT(e.user_id) FILTER (
            WHERE e.event_type = 'add_to_cart'
        ) AS cart_additions_60d,

        COUNT(e.user_id) FILTER (
            WHERE e.event_type = 'checkout'
        ) AS checkouts_60d

    FROM users AS u
    CROSS JOIN params AS p
    LEFT JOIN events AS e
        ON u.user_id = e.user_id
        AND e.event_at >= p.history_start
        AND e.event_at < p.snapshot_date

    GROUP BY u.user_id
)

SELECT
    os.user_id,
    os.country,
    os.orders_last_60d,
    ss.sessions_last_60d,
    ss.avg_session_duration_60d,
    es.events_last_60d,
    es.page_views_60d,
    es.product_views_60d,
    es.searches_60d,
    es.cart_additions_60d,
    es.checkouts_60d,
    os.target

FROM order_stats AS os
INNER JOIN session_stats AS ss
    ON os.user_id = ss.user_id
INNER JOIN event_stats AS es
    ON os.user_id = es.user_id