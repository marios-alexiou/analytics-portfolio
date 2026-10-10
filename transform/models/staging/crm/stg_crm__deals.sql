select
    deal_id,
    company_id,
    owner_id,
    pipeline,
    deal_stage,
    deal_stage in ('closed_won', 'closed_lost') as is_closed,
    deal_stage = 'closed_won' as is_won,
    cast(amount as {{ dbt.type_numeric() }}) as amount,
    upper(deal_currency_code) as currency,
    cast(created_at as {{ dbt.type_timestamp() }}) as created_at,
    cast(close_date as date) as close_date
from {{ source('crm', 'deals') }}
