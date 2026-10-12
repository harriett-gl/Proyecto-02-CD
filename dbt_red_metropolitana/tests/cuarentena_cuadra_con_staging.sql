-- Ningún registro se descarta en silencio: todo lo que entra a staging
-- termina en Silver o en cuarentena (por fuente). Devuelve descuadres.
-- Solo aplica mientras staging tiene datos (durante dbt build en el flujo).
with conteos as (
    select 'transmetro' as fuente,
           (select count(*) from {{ source('staging', 'transmetro_validaciones') }}) as entrada,
           (select count(*) from {{ ref('transmetro_validaciones') }})
         + (select count(*) from {{ ref('transmetro_duplicados') }}) as salida
    union all
    select 'transurbano',
           (select count(*) from {{ source('staging', 'transurbano_transacciones') }}),
           (select count(*) from {{ ref('transurbano_transacciones') }})
         + (select count(*) from {{ ref('transurbano_invalidos') }})
    union all
    select 'metroriel',
           (select count(*) from {{ source('staging', 'metroriel_viajes_raw') }}),
           (select count(*) from {{ ref('metroriel_viajes') }})
         + (select count(*) from {{ ref('metroriel_sin_salida') }})
    union all
    select 'aerometro',
           (select count(*) from {{ source('staging', 'aerometro_boardings') }}),
           (select count(*) from {{ ref('aerometro_boardings') }})
         + (select count(*) from {{ ref('aerometro_invalidos') }})
)
select *
from conteos
where entrada > 0
  and entrada <> salida
