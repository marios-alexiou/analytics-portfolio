select
    cast(date_range_start as date) as report_date,
    'linkedin_ads' as ad_platform,
    'li_' || {{ dbt.split_part('campaign_urn', "':'", 4) }} as campaign_id,
    campaign_name,
    cast(impressions as {{ dbt.type_int() }}) as impressions,
    cast(clicks as {{ dbt.type_int() }}) as clicks,
    cast(cost_in_usd as {{ dbt.type_numeric() }}) as spend,
    'USD' as spend_currency
from {{ source('marketing', 'linkedin_ads_analytics') }}
