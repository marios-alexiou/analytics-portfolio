with

-- Re-synced days are appended as exact copies; keep one row per day and campaign.
deduplicated as (
    {{ dbt_utils.deduplicate(
        relation=source('marketing', 'google_ads_campaign_stats'),
        partition_by='segments_date, campaign_id',
        order_by='_loaded_at desc',
    ) }}
)

select
    cast(segments_date as date) as report_date,
    'google_ads' as ad_platform,
    'gads_' || campaign_id as campaign_id,
    campaign_name,
    cast(impressions as {{ dbt.type_int() }}) as impressions,
    cast(clicks as {{ dbt.type_int() }}) as clicks,
    cast(cost_micros as {{ dbt.type_numeric() }}) / 1000000 as spend,
    upper(currency_code) as spend_currency
from deduplicated
