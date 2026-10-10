with

-- Webhooks are delivered at least once: keep the first delivery of each event.
deduplicated as (
    {{ dbt_utils.deduplicate(
        relation=source('billing', 'subscription_events'),
        partition_by='event_id',
        order_by='received_at',
    ) }}
)

select
    event_id,
    subscription_id,
    account_id,
    event_type,
    plan_id,
    previous_plan_id,
    billing_period,
    upper(currency) as currency,
    {{ minor_units_to_amount('unit_amount') }} as unit_amount,
    cast(occurred_at as {{ dbt.type_timestamp() }}) as occurred_at,
    cast(effective_at as {{ dbt.type_timestamp() }}) as effective_at,
    cast(received_at as {{ dbt.type_timestamp() }}) as received_at
from deduplicated
