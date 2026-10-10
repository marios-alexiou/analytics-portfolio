{#- Custom schemas are used as-is (staging, marts) rather than prefixed with the target schema. -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name | trim if custom_schema_name else target.schema }}
{%- endmacro %}
