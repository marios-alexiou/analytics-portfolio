with

parsed as (
    select
        {{ json_value('payload', '$.conversion.uuid') }} as conversion_id,
        {{ json_value('payload', '$.conversion.reference') }} as click_ref,
        {{ json_value('payload', '$.conversion.created') }} as converted_at_ms,
        {{ json_value('payload', '$.approval.status') }} as network_status,
        {{ json_value('payload', '$.payout_cents') }} as payout_cents,
        {{ json_value('payload', '$.payout_currency') }} as commission_currency,
        pulled_at
    from {{ source('affiliates', 'refera_conversions') }}
),

-- Each daily pull repeats the conversion; the latest pull has the current status.
latest as (
    {{ dbt_utils.deduplicate(relation='parsed', partition_by='conversion_id', order_by='pulled_at desc') }}
)

select
    'refera' as affiliate_network,
    conversion_id,
    click_ref,
    {{ epoch_ms_to_timestamp('converted_at_ms') }} as converted_at,
    case network_status
        when 'accepted' then 'approved'
        when 'rejected' then 'reversed'
        else 'pending'
    end as conversion_status,
    network_status,
    {{ minor_units_to_amount('payout_cents') }} as commission_amount,
    upper(commission_currency) as commission_currency,
    cast(pulled_at as {{ dbt.type_timestamp() }}) as last_pulled_at
from latest
