with

daily as (
    select
        fct_mrr_daily.*,
        dim_dates.month_start,
        dim_dates.is_period_end,
        dim_accounts.region,
        dim_accounts.acquisition_channel
    from {{ ref('fct_mrr_daily') }} as fct_mrr_daily
    inner join {{ ref('dim_dates') }} as dim_dates
        on fct_mrr_daily.date_day = dim_dates.date_day
    inner join {{ ref('dim_accounts') }} as dim_accounts
        on fct_mrr_daily.account_id = dim_accounts.account_id
),

-- Every segment gets a row every month, so a segment whose customers all churned still shows its starting MRR.
segments as (
    select distinct
        region,
        acquisition_channel
    from daily
),

months as (
    select distinct month_start from {{ ref('dim_dates') }}
),

movements as (
    select
        month_start,
        region,
        acquisition_channel,
        sum(case when mrr_movement = 'new' then mrr_change_usd else 0 end) as new_mrr_usd,
        sum(case when mrr_movement = 'expansion' then mrr_change_usd else 0 end) as expansion_mrr_usd,
        sum(case when mrr_movement = 'contraction' then mrr_change_usd else 0 end) as contraction_mrr_usd,
        sum(case when mrr_movement = 'churn' then mrr_change_usd else 0 end) as churned_mrr_usd,
        sum(case when mrr_movement = 'reactivation' then mrr_change_usd else 0 end) as reactivation_mrr_usd,
        sum(fx_effect_usd) as fx_effect_usd,
        count(distinct case when mrr_movement = 'new' then account_id end) as new_customers,
        count(distinct case when mrr_movement = 'reactivation' then account_id end) as reactivated_customers,
        count(distinct case when mrr_movement = 'churn' then account_id end) as churned_customers
    from daily
    group by 1, 2, 3
),

period_end as (
    select
        month_start,
        region,
        acquisition_channel,
        sum(mrr_usd) as ending_mrr_usd,
        count(distinct case when mrr_local > 0 then account_id end) as ending_customers
    from daily
    where is_period_end
    group by 1, 2, 3
),

monthly as (
    select
        months.month_start,
        segments.region,
        segments.acquisition_channel,
        coalesce(movements.new_mrr_usd, 0) as new_mrr_usd,
        coalesce(movements.expansion_mrr_usd, 0) as expansion_mrr_usd,
        coalesce(movements.contraction_mrr_usd, 0) as contraction_mrr_usd,
        coalesce(movements.churned_mrr_usd, 0) as churned_mrr_usd,
        coalesce(movements.reactivation_mrr_usd, 0) as reactivation_mrr_usd,
        coalesce(movements.fx_effect_usd, 0) as fx_effect_usd,
        coalesce(movements.new_customers, 0) as new_customers,
        coalesce(movements.reactivated_customers, 0) as reactivated_customers,
        coalesce(movements.churned_customers, 0) as churned_customers,
        coalesce(period_end.ending_mrr_usd, 0) as ending_mrr_usd,
        coalesce(period_end.ending_customers, 0) as ending_customers
    from months
    cross join segments
    left join movements
        on
            months.month_start = movements.month_start
            and segments.region = movements.region
            and segments.acquisition_channel = movements.acquisition_channel
    left join period_end
        on
            months.month_start = period_end.month_start
            and segments.region = period_end.region
            and segments.acquisition_channel = period_end.acquisition_channel
)

select
    month_start,
    region,
    acquisition_channel,
    coalesce(lag(ending_mrr_usd) over segment_timeline, 0) as starting_mrr_usd,
    new_mrr_usd,
    expansion_mrr_usd,
    contraction_mrr_usd,
    churned_mrr_usd,
    reactivation_mrr_usd,
    fx_effect_usd,
    ending_mrr_usd,
    coalesce(lag(ending_customers) over segment_timeline, 0) as starting_customers,
    new_customers,
    reactivated_customers,
    churned_customers,
    ending_customers
from monthly
window segment_timeline as (partition by region, acquisition_channel order by month_start)
