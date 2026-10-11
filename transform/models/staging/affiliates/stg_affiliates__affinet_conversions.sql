with

parsed as (
    select
        {{ json_value('payload', '$.id') }} as conversion_id,
        {{ json_value('payload', '$.click_ref') }} as click_ref,
        {{ json_value('payload', '$.event_date') }} as converted_at,
        {{ json_value('payload', '$.status') }} as network_status,
        {{ json_value('payload', '$.commission.amount') }} as commission_amount,
        {{ json_value('payload', '$.commission.currency') }} as commission_currency,
        pulled_at
    from {{ source('affiliates', 'affinet_conversions') }}
),

-- Each daily pull repeats the conversion; the latest pull has the current status.
latest as (
    {{ deduplicate_rows(relation='parsed', partition_by='conversion_id', order_by='pulled_at desc') }}
)

select
    'affinet' as affiliate_network,
    conversion_id,
    click_ref,
    cast(converted_at as {{ dbt.type_timestamp() }}) as converted_at,
    case network_status
        when 'approved' then 'approved'
        when 'declined' then 'reversed'
        else 'pending'
    end as conversion_status,
    network_status,
    cast(commission_amount as {{ dbt.type_numeric() }}) as commission_amount,
    upper(commission_currency) as commission_currency,
    cast(pulled_at as {{ dbt.type_timestamp() }}) as last_pulled_at
from latest
