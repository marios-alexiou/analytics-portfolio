-- MRR rebuilt from webhook events must match the billing system's own current state on the extract date.
-- A mismatch usually means an event was lost or has not been delivered yet.
with

billing_state as (
    select
        subscriptions.account_id,
        sum(
            case subscriptions.billing_period
                when 'annual' then subscriptions.unit_amount / 12
                else subscriptions.unit_amount
            end
        ) as mrr_local
    from {{ ref('stg_billing__subscriptions') }} as subscriptions
    inner join {{ ref('stg_app_db__accounts') }} as accounts
        on subscriptions.account_id = accounts.account_id
    where
        not accounts.is_internal
        and subscriptions.status in ('active', 'past_due')
    group by 1
),

from_events as (
    select
        account_id,
        mrr_local
    from {{ ref('fct_mrr_daily') }}
    where
        date_day = cast('{{ var("as_of_date") }}' as date)
        and mrr_local > 0
)

select
    coalesce(billing_state.account_id, from_events.account_id) as account_id,
    billing_state.mrr_local as billing_mrr_local,
    from_events.mrr_local as event_mrr_local
from billing_state
full outer join from_events
    on billing_state.account_id = from_events.account_id
where
    billing_state.account_id is null
    or from_events.account_id is null
    or abs(billing_state.mrr_local - from_events.mrr_local) > 0.01
