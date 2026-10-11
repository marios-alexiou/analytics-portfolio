with

dates as (
    select date_day from {{ ref('dim_dates') }}
),

published as (
    select * from {{ ref('stg_finance__fx_rates') }}
),

currencies as (
    select distinct currency from published
    union all
    select 'USD' as currency
),

spine as (
    select
        dates.date_day,
        currencies.currency
    from dates
    cross join currencies
)

-- Rates are published on business days only: weekends and holidays carry the last published rate.
select
    spine.date_day,
    spine.currency,
    case
        when spine.currency = 'USD' then 1
        else last_value(published.usd_per_unit ignore nulls) over (
            partition by spine.currency
            order by spine.date_day
            rows between unbounded preceding and current row
        )
    end as usd_per_unit,
    published.rate_date is not null as is_published_rate
from spine
left join published
    on
        spine.date_day = published.rate_date
        and spine.currency = published.currency
