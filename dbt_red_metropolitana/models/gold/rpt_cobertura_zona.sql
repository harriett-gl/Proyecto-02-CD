{{ config(materialized='view') }}

/*
    COBERTURA Y DEMANDA POR ZONA  (Fase 02 - tablero 2.1 y caso MetroRiel)

    Grano: una fila por zona del área metropolitana.

    El universo de zonas une:
      - las zonas donde algún operador registró actividad (gold.dim_zona), y
      - las zonas de residencia declaradas en el padrón vigente (Silver).
    Así aparecen también las zonas donde vive gente pero ningún modo opera,
    que es exactamente la pregunta de cobertura del tablero.

    Se materializa como vista: no duplica datos y no altera los conteos de
    tablas Gold reportados en la auditoría de idempotencia.
*/

with zonas_residencia as (

    select
        {{ normalizar_zona('zona_residencia') }} as zona_nombre,
        count(*) as residentes_padron,
        count(*) filter (where activo) as residentes_activos

    from {{ ref('dim_usuario_actual') }}

    where nullif(trim(zona_residencia), '') is not null

    group by 1

),

universo as (

    select zona_nombre from {{ ref('dim_zona') }}
    union
    select zona_nombre from zonas_residencia

),

abordajes as (

    select
        zona_nombre,
        count(*) filter (where modo_nombre = 'TRANSMETRO') as abordajes_transmetro,
        count(*) filter (where modo_nombre = 'TRANSURBANO') as abordajes_transurbano,
        count(*) filter (where modo_nombre = 'AEROMETRO') as abordajes_aerometro

    from {{ ref('fct_abordajes') }}

    group by zona_nombre

),

metroriel_origen as (

    select zona_entrada as zona_nombre, count(*) as viajes_metroriel_origen
    from {{ ref('fct_viajes_metroriel') }}
    group by 1

),

metroriel_destino as (

    select zona_salida as zona_nombre, count(*) as viajes_metroriel_destino
    from {{ ref('fct_viajes_metroriel') }}
    group by 1

),

consolidado as (

    select
        md5(universo.zona_nombre) as zona_sk,
        universo.zona_nombre,

        coalesce(residencia.residentes_padron, 0) as residentes_padron,
        coalesce(residencia.residentes_activos, 0) as residentes_activos,

        coalesce(abordajes.abordajes_transmetro, 0) as abordajes_transmetro,
        coalesce(abordajes.abordajes_transurbano, 0) as abordajes_transurbano,
        coalesce(abordajes.abordajes_aerometro, 0) as abordajes_aerometro,
        coalesce(origen.viajes_metroriel_origen, 0) as viajes_metroriel_origen,
        coalesce(destino.viajes_metroriel_destino, 0) as viajes_metroriel_destino

    from universo

    left join zonas_residencia residencia
        on universo.zona_nombre = residencia.zona_nombre

    left join abordajes
        on universo.zona_nombre = abordajes.zona_nombre

    left join metroriel_origen origen
        on universo.zona_nombre = origen.zona_nombre

    left join metroriel_destino destino
        on universo.zona_nombre = destino.zona_nombre

)

select
    *,

    (abordajes_transmetro > 0)::int
      + (abordajes_transurbano > 0)::int
      + (abordajes_aerometro > 0)::int
      + (viajes_metroriel_origen + viajes_metroriel_destino > 0)::int
        as modos_con_servicio,

    abordajes_transmetro + abordajes_transurbano + abordajes_aerometro
      + viajes_metroriel_origen + viajes_metroriel_destino = 0
        as sin_servicio,

    zona_nombre in {{ zonas_trazado_metroriel() }}
        as en_trazado_metroriel,

    -- Demanda que existe SIN MetroRiel: es la base justa para evaluar si
    -- el trazado va donde más se necesita (no cuenta la demanda que el
    -- propio MetroRiel genera).
    abordajes_transmetro + abordajes_transurbano + abordajes_aerometro
        as demanda_sin_metroriel,

    abordajes_transmetro + abordajes_transurbano + abordajes_aerometro
      + viajes_metroriel_origen
        as demanda_total,

    rank() over (
        order by abordajes_transmetro + abordajes_transurbano
                 + abordajes_aerometro desc
    ) as ranking_demanda_sin_metroriel

from consolidado
