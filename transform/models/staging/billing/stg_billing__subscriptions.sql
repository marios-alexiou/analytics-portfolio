select
    subscription_id,
    account_id,
    status,
    plan_id,
    billing_period,
    upper(currency) as currency,
    {{ minor_units_to_amount('unit_amount') }} as unit_amount,
    cast(cancel_at_period_end as boolean) as cancel_at_period_end,
    cancel_reason,
    cast(started_at as {{ dbt.type_timestamp() }}) as started_at,
    cast(cancel_requested_at as {{ dbt.type_timestamp() }}) as cancel_requested_at,
    cast(ended_at as {{ dbt.type_timestamp() }}) as ended_at,
    cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at
from {{ source('billing', 'subscriptions') }}
