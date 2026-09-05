{#
    Use the custom schema exactly as configured (raw, staging, marts)
    instead of dbt's default "<target_schema>_<custom_schema>" naming,
    so the DuckDB catalog reads cleanly as raw / staging / marts.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
