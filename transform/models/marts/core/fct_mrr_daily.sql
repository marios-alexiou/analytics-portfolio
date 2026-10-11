with

periods as (
    select * from {{ ref('int_subscription_periods') }}
),

accounts as (
    select * from {{ ref('stg_app_db__accounts') }}
),

dates as (
    select date_day from {{ ref('dim_dates') }}
),

fx as (
    select * from {{ ref('int_fx_rates_daily') }}
),

-- MRR is the state at the end of each day: a period counts from the day it starts until the day before it ends.
active_days as (
    select
        periods.account_id,
        dates.date_day,
        periods.currency,
        sum(periods.mrr_local) as mrr_local
    from periods
    inner join dates
        on
            dates.date_day >= cast(periods.valid_from as date)
            and (periods.valid_to is null or dates.date_day < cast(periods.valid_to as date))
    inner join accounts
        on periods.account_id = accounts.account_id
    where not accounts.is_internal
    group by 1, 2, 3
),

-- Add a zero-MRR row on the first day an account stops paying, so the churn is recorded on that day.
churn_days as (
    select
        account_id,
        cast({{ dbt.dateadd('day', 1, 'date_day') }} as date) as date_day,
        currency,
        0 as mrr_local
    from (
        select
            account_id,
            date_day,
            currency,
            lead(date_day) over (partition by account_id order by date_day) as next_active_day
        from active_days
    ) as with_next
    where
        (next_active_day is null or next_active_day > cast({{ dbt.dateadd('day', 1, 'date_day') }} as date))
        and date_day < cast('{{ var("as_of_date") }}' as date)
),

account_days as (
    select
        account_day_rows.account_id,
        account_day_rows.date_day,
        account_day_rows.currency,
        account_day_rows.mrr_local,
        fx.usd_per_unit,
        account_day_rows.mrr_local * fx.usd_per_unit as mrr_usd
    from (
        select * from active_days
        union all
        select * from churn_days
    ) as account_day_rows
    inner join fx
        on
            account_day_rows.date_day = fx.date_day
            and account_day_rows.currency = fx.currency
),

with_previous as (
    select
        *,
        coalesce(lag(mrr_local) over account_timeline, 0) as previous_mrr_local,
        coalesce(lag(mrr_usd) over account_timeline, 0) as previous_mrr_usd,
        coalesce(sum(case when mrr_local > 0 then 1 else 0 end) over (
            partition by account_id
            order by date_day
            rows between unbounded preceding and 1 preceding
        ), 0) as prior_paying_days
    from account_days
    window account_timeline as (partition by account_id order by date_day)
)

select
    date_day,
    account_id,
    currency,
    mrr_local,
    previous_mrr_local,
    usd_per_unit,
    mrr_usd,
    previous_mrr_usd,
    case
        when previous_mrr_local = 0 and mrr_local > 0 and prior_paying_days = 0 then 'new'
        when previous_mrr_local = 0 and mrr_local > 0 then 'reactivation'
        when previous_mrr_local > 0 and mrr_local = 0 then 'churn'
        when mrr_local > previous_mrr_local then 'expansion'
        when mrr_local < previous_mrr_local then 'contraction'
        else 'unchanged'
    end as mrr_movement,
    -- Customer-driven change valued at today's rate; the rest of the USD change is exchange-rate movement.
    (mrr_local - previous_mrr_local) * usd_per_unit as mrr_change_usd,
    mrr_usd - previous_mrr_usd - (mrr_local - previous_mrr_local) * usd_per_unit as fx_effect_usd
from with_previous
