select
    cast(date_start as date) as report_date,
    'meta_ads' as ad_platform,
    'meta_' || campaign_id as campaign_id,
    campaign_name,
    cast(impressions as {{ dbt.type_int() }}) as impressions,
    cast(clicks as {{ dbt.type_int() }}) as clicks,
    cast(spend as {{ dbt.type_numeric() }}) as spend,
    upper(account_currency) as spend_currency
from {{ source('marketing', 'meta_ads_insights') }}
