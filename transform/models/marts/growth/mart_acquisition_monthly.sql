with

months as (
    select distinct month_start from {{ ref('dim_dates') }}
),

channels as (
    select * from {{ ref('acquisition_channels') }}
),

accounts as (
    select * from {{ ref('dim_accounts') }}
    where not is_internal
),

signups as (
    select
        cast({{ dbt.date_trunc('month', 'created_at') }} as date) as month_start,
        acquisition_channel,
        count(*) as signups
    from accounts
    group by 1, 2
),

new_customers as (
    select
        cast({{ dbt.date_trunc('month', 'first_paid_at') }} as date) as month_start,
        acquisition_channel,
        count(*) as new_customers,
        sum(first_mrr_usd) as new_mrr_usd
    from accounts
    where first_paid_at is not null
    group by 1, 2
),

ad_spend as (
    select
        cast({{ dbt.date_trunc('month', 'report_date') }} as date) as month_start,
        acquisition_channel,
        sum(impressions) as impressions,
        sum(clicks) as clicks,
        sum(spend_usd) as ad_spend_usd
    from {{ ref('int_ad_spend_daily') }}
    group by 1, 2
),

-- Commission is a cost from the month of the conversion; reversed conversions are never paid.
affiliate as (
    select
        cast({{ dbt.date_trunc('month', 'converted_at') }} as date) as month_start,
        'partner' as acquisition_channel,
        sum(commission_usd) as affiliate_commission_usd
    from {{ ref('int_affiliate_conversions') }}
    where conversion_status != 'reversed'
    group by 1, 2
)

-- Counts and sums only: CAC (acquisition_cost_usd / new_customers) and payback are computed in the BI tool.
select
    months.month_start,
    channels.acquisition_channel,
    channels.channel_group,
    channels.is_paid,
    coalesce(signups.signups, 0) as signups,
    coalesce(new_customers.new_customers, 0) as new_customers,
    coalesce(new_customers.new_mrr_usd, 0) as new_mrr_usd,
    coalesce(ad_spend.impressions, 0) as impressions,
    coalesce(ad_spend.clicks, 0) as clicks,
    coalesce(ad_spend.ad_spend_usd, 0) as ad_spend_usd,
    coalesce(affiliate.affiliate_commission_usd, 0) as affiliate_commission_usd,
    coalesce(ad_spend.ad_spend_usd, 0) + coalesce(affiliate.affiliate_commission_usd, 0) as acquisition_cost_usd
from months
cross join channels
left join signups
    on
        months.month_start = signups.month_start
        and channels.acquisition_channel = signups.acquisition_channel
left join new_customers
    on
        months.month_start = new_customers.month_start
        and channels.acquisition_channel = new_customers.acquisition_channel
left join ad_spend
    on
        months.month_start = ad_spend.month_start
        and channels.acquisition_channel = ad_spend.acquisition_channel
left join affiliate
    on
        months.month_start = affiliate.month_start
        and channels.acquisition_channel = affiliate.acquisition_channel
