select
    owner_id,
    full_name as owner_name,
    lower(email) as owner_email,
    team as sales_team
from {{ source('crm', 'owners') }}
