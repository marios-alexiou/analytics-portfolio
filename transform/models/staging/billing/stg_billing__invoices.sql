select
    invoice_id,
    subscription_id,
    account_id,
    billing_reason,
    status,
    upper(currency) as currency,
    {{ minor_units_to_amount('amount_due') }} as amount_due,
    {{ minor_units_to_amount('amount_refunded') }} as amount_refunded,
    cast(period_start as {{ dbt.type_timestamp() }}) as period_start,
    cast(period_end as {{ dbt.type_timestamp() }}) as period_end,
    cast(issued_at as {{ dbt.type_timestamp() }}) as issued_at,
    cast(paid_at as {{ dbt.type_timestamp() }}) as paid_at,
    cast(refunded_at as {{ dbt.type_timestamp() }}) as refunded_at
from {{ source('billing', 'invoices') }}
