with

accounts as (
    select * from {{ ref('stg_app_db__accounts') }}
),

countries as (
    select * from {{ ref('country_codes') }}
),

first_period as (
    {{ deduplicate_rows(
        relation=ref('int_subscription_periods'),
        partition_by='account_id',
        order_by='valid_from',
    ) }}
),

first_mrr as (
    select
        account_id,
        mrr_change_usd as first_mrr_usd
    from {{ ref('fct_mrr_daily') }}
    where mrr_movement = 'new'
),

current_mrr as (
    select
        account_id,
        mrr_local as current_mrr_local,
        mrr_usd as current_mrr_usd
    from {{ ref('fct_mrr_daily') }}
    where date_day = cast('{{ var("as_of_date") }}' as date)
),

subscriptions as (
    select
        account_id,
        count(*) as subscription_count
    from {{ ref('stg_billing__subscriptions') }}
    group by 1
),

companies as (
    select * from {{ ref('stg_crm__companies') }}
),

owners as (
    select * from {{ ref('stg_crm__owners') }}
)

select
    accounts.account_id,
    accounts.company_name,
    accounts.email_domain,
    accounts.is_internal,
    accounts.country_code,
    countries.country_name,
    countries.region,
    accounts.company_size,
    accounts.acquisition_channel,
    accounts.utm_campaign as acquisition_campaign_id,
    accounts.created_at,
    accounts.trial_ends_at,
    first_period.valid_from as first_paid_at,
    first_period.plan_id as first_plan_id,
    first_period.billing_period as first_billing_period,
    first_period.currency as billing_currency,
    first_mrr.first_mrr_usd,
    {{ dbt.datediff(
        'accounts.created_at',
        'first_period.valid_from',
        'day',
    ) }} as days_to_convert,
    first_period.valid_from <= accounts.trial_ends_at as converted_in_trial,
    coalesce(subscriptions.subscription_count, 0) as subscription_count,
    coalesce(current_mrr.current_mrr_local, 0) as current_mrr_local,
    coalesce(current_mrr.current_mrr_usd, 0) as current_mrr_usd,
    case
        when accounts.is_internal then 'internal'
        when current_mrr.current_mrr_local > 0 then 'active'
        when first_period.account_id is not null then 'churned'
        when
            accounts.trial_ends_at > cast('{{ var("as_of_date") }}' as {{ dbt.type_timestamp() }})
            then 'trialing'
        else 'trial_expired'
    end as customer_status,
    coalesce(crm_by_account.company_id, crm_by_domain.company_id) as crm_company_id,
    case
        when crm_by_account.company_id is not null then 'account_id'
        when crm_by_domain.company_id is not null then 'email_domain'
    end as crm_match_method,
    owners.owner_name as account_owner,
    owners.sales_team
from accounts
left join countries
    on accounts.country_code = countries.country_code
left join first_period
    on accounts.account_id = first_period.account_id
left join first_mrr
    on accounts.account_id = first_mrr.account_id
left join current_mrr
    on accounts.account_id = current_mrr.account_id
left join subscriptions
    on accounts.account_id = subscriptions.account_id
-- Reps link only some CRM companies to a workspace; fall back to the signup email domain.
left join companies as crm_by_account
    on accounts.account_id = crm_by_account.account_id
left join companies as crm_by_domain
    on
        crm_by_account.company_id is null
        and crm_by_domain.account_id is null
        and accounts.email_domain = crm_by_domain.company_domain
        and not accounts.is_internal
left join owners
    on coalesce(crm_by_account.owner_id, crm_by_domain.owner_id) = owners.owner_id
