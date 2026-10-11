with

accounts as (
    select
        *,
        cast({{ dbt.date_trunc('month', 'created_at') }} as date) as signup_month,
        {{ dbt.dateadd('day', 30, 'created_at') }} <= cast('{{ var("as_of_date") }}' as {{ dbt.type_timestamp() }})
            as has_30_days_of_history
    from {{ ref('dim_accounts') }}
    where not is_internal
)

-- Counts only: rates are computed in the BI tool from these sums so they stay correct at any roll-up.
select
    signup_month,
    acquisition_channel,
    region,
    company_size,
    count(*) as signups,
    sum(case when trial_ends_at <= cast('{{ var("as_of_date") }}' as {{ dbt.type_timestamp() }}) then 1 else 0 end)
        as completed_trials,
    sum(case when converted_in_trial then 1 else 0 end) as converted_in_trial,
    sum(case when has_30_days_of_history then 1 else 0 end) as signups_with_30_days,
    sum(case when has_30_days_of_history and days_to_convert <= 30 then 1 else 0 end) as converted_within_30_days,
    sum(case when first_paid_at is not null then 1 else 0 end) as converted_to_date,
    sum(coalesce(days_to_convert, 0)) as total_days_to_convert,
    sum(coalesce(first_mrr_usd, 0)) as first_mrr_usd
from accounts
group by 1, 2, 3, 4
