with

traffic as (
    select
        cast({{ dbt.date_trunc('month', 'report_date') }} as date) as month_start,
        channel_group,
        sum(sessions) as sessions,
        sum(engaged_sessions) as engaged_sessions
    from {{ ref('stg_marketing__web_traffic') }}
    group by 1, 2
),

-- Signups and customers are rolled up to the web tool's channel groups so the funnel compares like with like.
acquisition as (
    select
        month_start,
        channel_group,
        sum(signups) as signups,
        sum(new_customers) as new_customers
    from {{ ref('mart_acquisition_monthly') }}
    group by 1, 2
)

select
    coalesce(traffic.month_start, acquisition.month_start) as month_start,
    coalesce(traffic.channel_group, acquisition.channel_group) as channel_group,
    coalesce(traffic.sessions, 0) as sessions,
    coalesce(traffic.engaged_sessions, 0) as engaged_sessions,
    coalesce(acquisition.signups, 0) as signups,
    coalesce(acquisition.new_customers, 0) as new_customers
from traffic
full outer join acquisition
    on
        traffic.month_start = acquisition.month_start
        and traffic.channel_group = acquisition.channel_group
