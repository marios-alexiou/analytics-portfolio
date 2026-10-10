select
    cast(rate_date as date) as rate_date,
    upper(currency) as currency,
    cast(usd_per_unit as {{ dbt.type_numeric() }}) as usd_per_unit
from {{ source('finance', 'fx_rates') }}
