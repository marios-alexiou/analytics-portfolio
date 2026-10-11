with

google as (
    select * from {{ ref('stg_marketing__google_ads') }}
),

meta as (
    select * from {{ ref('stg_marketing__meta_ads') }}
),

linkedin as (
    select * from {{ ref('stg_marketing__linkedin_ads') }}
),

unioned as (
    select * from google
    union all
    select * from meta
    union all
    select * from linkedin
)

select
    unioned.report_date,
    unioned.ad_platform,
    channels.acquisition_channel,
    unioned.campaign_id,
    unioned.campaign_name,
    unioned.impressions,
    unioned.clicks,
    unioned.spend,
    unioned.spend_currency,
    unioned.spend * fx.usd_per_unit as spend_usd
from unioned
left join {{ ref('acquisition_channels') }} as channels
    on unioned.ad_platform = channels.ad_platform
left join {{ ref('int_fx_rates_daily') }} as fx
    on
        unioned.report_date = fx.date_day
        and unioned.spend_currency = fx.currency
