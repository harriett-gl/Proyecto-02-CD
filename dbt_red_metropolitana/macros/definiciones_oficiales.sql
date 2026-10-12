{#
    Definiciones oficiales compartidas (ver docs/gobernanza.md).
    Se usan en Gold y en Features para que todos midan igual.
#}

{# Hora pico oficial: 06:00-08:59 y 16:00-18:59 (hora local). #}
{% macro es_hora_pico(columna_hora) -%}
    ({{ columna_hora }} in (6, 7, 8, 16, 17, 18))
{%- endmacro %}

{# Zonas del trazado propuesto de MetroRiel (enunciado del proyecto). #}
{% macro zonas_trazado_metroriel() -%}
    ('Zona 12', 'Zona 8', 'Zona 1', 'Zona 6', 'Zona 17')
{%- endmacro %}

{# Normalización oficial de zona: 'Z10', 'ZONA 10', 'zona 10' -> 'Zona 10'. #}
{% macro normalizar_zona(columna) -%}
    case
        when upper(trim({{ columna }})) ~ '^ZONA[ ]*[0-9]+$'
            then 'Zona ' || regexp_replace(upper(trim({{ columna }})), '[^0-9]', '', 'g')
        when upper(trim({{ columna }})) ~ '^Z[0-9]+$'
            then 'Zona ' || substring(upper(trim({{ columna }})) from 2)
        else initcap(lower(trim({{ columna }})))
    end
{%- endmacro %}
