{#- Warehouse-specific SQL lives here so models stay identical on DuckDB and BigQuery. -#}

{% macro json_value(column, path) -%}
    {{ return(adapter.dispatch('json_value')(column, path)) }}
{%- endmacro %}

{% macro default__json_value(column, path) -%}
    json_value({{ column }}, '{{ path }}')
{%- endmacro %}

{% macro duckdb__json_value(column, path) -%}
    json_extract_string({{ column }}, '{{ path }}')
{%- endmacro %}


{% macro epoch_ms_to_timestamp(column) -%}
    {{ return(adapter.dispatch('epoch_ms_to_timestamp')(column)) }}
{%- endmacro %}

{% macro default__epoch_ms_to_timestamp(column) -%}
    timestamp_millis(cast({{ column }} as int64))
{%- endmacro %}

{% macro duckdb__epoch_ms_to_timestamp(column) -%}
    epoch_ms(cast({{ column }} as bigint))
{%- endmacro %}


{#- Parse a local-time string and return it as a UTC timestamp. -#}
{% macro parse_local_timestamp(column, format, timezone) -%}
    {{ return(adapter.dispatch('parse_local_timestamp')(column, format, timezone)) }}
{%- endmacro %}

{% macro default__parse_local_timestamp(column, format, timezone) -%}
    timestamp(parse_datetime('{{ format }}', {{ column }}), '{{ timezone }}')
{%- endmacro %}

{% macro duckdb__parse_local_timestamp(column, format, timezone) -%}
    ((strptime({{ column }}, '{{ format }}') at time zone '{{ timezone }}') at time zone 'UTC')
{%- endmacro %}


{#- Strip protocol, www. and trailing slashes so hand-typed domains can be joined. -#}
{% macro normalize_domain(column) -%}
    {{ return(adapter.dispatch('normalize_domain')(column)) }}
{%- endmacro %}

{% macro default__normalize_domain(column) -%}
    regexp_replace(lower(trim({{ column }})), r'^(https?://)?(www\.)?|/+$', '')
{%- endmacro %}

{% macro duckdb__normalize_domain(column) -%}
    regexp_replace(lower(trim({{ column }})), '^(https?://)?(www\.)?|/+$', '', 'g')
{%- endmacro %}
