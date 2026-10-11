with

conversions as (
    select * from {{ ref('stg_affiliates__affinet_conversions') }}
    union all
    select * from {{ ref('stg_affiliates__linkloop_conversions') }}
    union all
    select * from {{ ref('stg_affiliates__refera_conversions') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['conversions.affiliate_network', 'conversions.conversion_id']) }}
        as affiliate_conversion_id,
    conversions.affiliate_network,
    conversions.conversion_id,
    conversions.click_ref,
    app_accounts.account_id,
    conversions.converted_at,
    conversions.conversion_status,
    conversions.commission_amount,
    conversions.commission_currency,
    conversions.commission_amount * fx.usd_per_unit as commission_usd,
    conversions.last_pulled_at
from conversions
left join {{ ref('stg_app_db__accounts') }} as app_accounts
    on conversions.click_ref = app_accounts.affiliate_click_ref
left join {{ ref('int_fx_rates_daily') }} as fx
    on
        cast(conversions.converted_at as date) = fx.date_day
        and conversions.commission_currency = fx.currency
