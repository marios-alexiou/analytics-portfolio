with

spine as (
    {{ dbt_utils.date_spine(
        datepart='day',
        start_date="cast('" ~ var('start_date') ~ "' as date)",
        end_date=dbt.dateadd('day', 1, "cast('" ~ var('as_of_date') ~ "' as date)"),
    ) }}
)

select
    cast(date_day as date) as date_day,
    cast({{ dbt.date_trunc('month', 'date_day') }} as date) as month_start,
    cast({{ dbt.last_day('date_day', 'month') }} as date) as month_end,
    cast(date_day as date) = cast({{ dbt.last_day('date_day', 'month') }} as date)
    or cast(date_day as date) = cast('{{ var("as_of_date") }}' as date) as is_period_end,
    extract(year from date_day) as calendar_year,
    extract(quarter from date_day) as calendar_quarter,
    extract(month from date_day) as calendar_month
from spine
