with

events as (
    select * from {{ ref('stg_billing__subscription_events') }}
),

ordered as (
    select
        subscription_id,
        account_id,
        event_type,
        plan_id,
        billing_period,
        currency,
        unit_amount,
        effective_at as valid_from,
        lead(effective_at) over (
            partition by subscription_id
            order by effective_at, occurred_at
        ) as valid_to
    from events
)

-- A cancellation only closes the preceding period; it does not open one.
select
    {{ dbt_utils.generate_surrogate_key(['subscription_id', 'valid_from']) }} as subscription_period_id,
    subscription_id,
    account_id,
    plan_id,
    billing_period,
    currency,
    unit_amount,
    case billing_period
        when 'annual' then unit_amount / 12
        else unit_amount
    end as mrr_local,
    valid_from,
    valid_to
from ordered
where event_type != 'subscription_cancelled'
