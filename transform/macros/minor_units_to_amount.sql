{#- Billing amounts arrive in minor units (cents); convert to the currency's major unit. -#}
{% macro minor_units_to_amount(column) -%}
    cast({{ column }} as {{ dbt.type_numeric() }}) / 100
{%- endmacro %}
