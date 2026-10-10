with

parsed as (
    select
        {{ json_value('payload', '$.transactionId') }} as conversion_id,
        {{ json_value('payload', '$.subId') }} as click_ref,
        {{ json_value('payload', '$.date') }} as converted_at_local,
        {{ json_value('payload', '$.state') }} as network_status,
        {{ json_value('payload', '$.commissionAmount') }} as commission_amount,
        {{ json_value('payload', '$.currency') }} as commission_currency,
        pulled_at
    from {{ source('affiliates', 'linkloop_conversions') }}
),

-- Each daily pull repeats the conversion; the latest pull has the current status.
latest as (
    {{ dbt_utils.deduplicate(relation='parsed', partition_by='conversion_id', order_by='pulled_at desc') }}
)

select
    'linkloop' as affiliate_network,
    conversion_id,
    click_ref,
    {{ parse_local_timestamp('converted_at_local', '%d/%m/%Y %H:%M', 'Europe/London') }} as converted_at,
    case network_status
        when 'CONFIRMED' then 'approved'
        when 'DECLINED' then 'reversed'
        else 'pending'
    end as conversion_status,
    network_status,
    cast(commission_amount as {{ dbt.type_numeric() }}) as commission_amount,
    upper(commission_currency) as commission_currency,
    cast(pulled_at as {{ dbt.type_timestamp() }}) as last_pulled_at
from latest
