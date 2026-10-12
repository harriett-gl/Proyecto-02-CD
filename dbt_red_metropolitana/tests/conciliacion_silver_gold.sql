-- Prueba de fuego de gobernanza: el mismo indicador calculado desde Silver
-- y desde Gold debe dar el mismo número. Devuelve las diferencias.
with silver as (
    select 'TRANSMETRO' as modo, count(*) as n from {{ ref('transmetro_validaciones') }}
    union all
    select 'TRANSURBANO', count(*) from {{ ref('transurbano_transacciones') }} where transaccion_aprobada
    union all
    select 'AEROMETRO', count(*) from {{ ref('aerometro_boardings') }}
    union all
    select 'METRORIEL', count(*) from {{ ref('metroriel_viajes') }}
),
gold as (
    select modo_nombre as modo, count(*) as n from {{ ref('fct_abordajes') }} group by 1
    union all
    select 'METRORIEL', count(*) from {{ ref('fct_viajes_metroriel') }}
)
select silver.modo, silver.n as filas_silver, gold.n as filas_gold
from silver
full join gold on silver.modo = gold.modo
where silver.n is distinct from gold.n
