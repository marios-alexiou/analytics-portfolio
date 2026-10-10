select
    company_id,
    trim(name) as company_name,
    {{ normalize_domain('domain') }} as company_domain,
    upper(country) as country_code,
    fieldcraft_account_id as account_id,
    owner_id,
    lifecycle_stage,
    cast(created_at as {{ dbt.type_timestamp() }}) as created_at,
    cast(updated_at as {{ dbt.type_timestamp() }}) as updated_at
from {{ source('crm', 'companies') }}
