with

source as (
    select * from {{ source('app_db', 'accounts') }}
),

countries as (
    select * from {{ ref('country_codes') }}
)

select
    source.account_id,
    trim(source.company_name) as company_name,
    lower(trim(source.email)) as email,
    {{ dbt.split_part('lower(trim(source.email))', "'@'", 2) }} as email_domain,
    {{ dbt.split_part('lower(trim(source.email))', "'@'", 2) }} = '{{ var("internal_email_domain") }}' as is_internal,
    countries.country_code,
    source.company_size,
    source.utm_source,
    source.utm_medium,
    source.utm_campaign,
    source.affiliate_click_ref,
    case
        when source.utm_medium = 'affiliate' then 'partner'
        when source.utm_medium = 'cpc' then 'paid_search'
        when source.utm_source = 'linkedin' then 'linkedin'
        when source.utm_medium = 'paid_social' then 'paid_social'
        when source.utm_medium = 'organic' then 'organic'
        when source.utm_medium = 'referral' then 'referral'
        else 'direct'
    end as acquisition_channel,
    cast(source.created_at as {{ dbt.type_timestamp() }}) as created_at,
    cast(source.trial_ends_at as {{ dbt.type_timestamp() }}) as trial_ends_at
from source
-- The signup form accepts free text: match the ISO code or the country name.
left join countries
    on
        upper(trim(source.country_code)) = countries.country_code
        or lower(trim(source.country_code)) = lower(countries.country_name)
