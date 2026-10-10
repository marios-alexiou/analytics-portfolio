select
    cast(date as date) as report_date,
    session_default_channel_group as channel_group,
    cast(sessions as {{ dbt.type_int() }}) as sessions,
    cast(engaged_sessions as {{ dbt.type_int() }}) as engaged_sessions
from {{ source('marketing', 'web_traffic_daily') }}
