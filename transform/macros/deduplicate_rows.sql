{#- Keep the first row per key by `order_by`.
    Replaces dbt_utils.deduplicate, whose default implementation natural-joins on every column and
    silently drops rows that contain a NULL. -#}
{% macro deduplicate_rows(relation, partition_by, order_by) -%}
    select *
    from {{ relation }}
    where true  -- BigQuery only accepts QUALIFY alongside WHERE, GROUP BY or HAVING
    qualify row_number() over (partition by {{ partition_by }} order by {{ order_by }}) = 1
{%- endmacro %}
