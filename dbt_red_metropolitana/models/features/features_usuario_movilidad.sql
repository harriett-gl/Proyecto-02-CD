{{ config(
    materialized='table',
    schema='features'
) }}

/*
    FEATURES DE MOVILIDAD POR USUARIO  (Fase 02 - sección 2.3)

    Grano:        una fila por usuario (usuario_sk) con al menos un viaje
                  válido hasta la fecha de corte.
    Fuente:       SOLO capa Silver (detalle atómico por evento). No lee Gold,
                  porque Gold ya agregó a un grano de negocio.
    Fecha corte:  variable dbt `fecha_corte` (por defecto 2026-07-15, último
                  día con datos). Ningún evento posterior entra al cálculo,
                  para evitar fuga de información si se entrena un modelo.
                  Cambiar con:  dbt build --vars '{fecha_corte: "2026-07-01"}'
    Seudonimización: solo se expone usuario_sk, nunca la tarjeta original.
*/

{% set fecha_corte = var('fecha_corte', '2026-07-15') %}

with eventos as (

    -- Transmetro: validaciones sin duplicados de torniquete
    select
        'TRANSMETRO' as modo,
        usuario_origen_id,
        fecha_hora_local,
        zona,
        monto_gtq,
        true as viaje_valido
    from {{ ref('transmetro_validaciones') }}

    union all

    -- Transurbano: se conservan rechazadas para contarlas aparte
    select
        'TRANSURBANO',
        usuario_origen_id,
        fecha_hora_local,
        zona,
        monto_gtq,
        transaccion_aprobada
    from {{ ref('transurbano_transacciones') }}

    union all

    -- MetroRiel: el viaje cuenta en su estación/zona de entrada
    select
        'METRORIEL',
        usuario_origen_id,
        fecha_hora_entrada,
        zona_entrada,
        monto_gtq,
        true
    from {{ ref('metroriel_viajes') }}

    union all

    -- Aerómetro: hora ya convertida de UTC a hora local en Silver
    select
        'AEROMETRO',
        usuario_origen_id,
        fecha_hora_local,
        zona,
        monto_gtq,
        true
    from {{ ref('aerometro_boardings') }}

),

eventos_usuario as (

    select
        usuario.usuario_sk,
        evento.modo,
        evento.fecha_hora_local,
        evento.fecha_hora_local::date as fecha,
        {{ normalizar_zona('evento.zona') }} as zona,
        evento.monto_gtq,
        evento.viaje_valido,
        {{ es_hora_pico('extract(hour from evento.fecha_hora_local)') }}
            as en_hora_pico,
        extract(isodow from evento.fecha_hora_local) in (6, 7)
            as en_fin_semana

    from eventos evento

    inner join {{ ref('dim_usuario_conformado') }} usuario
        on evento.modo = usuario.modo
       and evento.usuario_origen_id = usuario.usuario_origen_id

    where evento.fecha_hora_local::date <= date '{{ fecha_corte }}'

),

viajes as (

    select *
    from eventos_usuario
    where viaje_valido

),

agregado as (

    select
        usuario_sk,

        count(*) filter (
            where fecha > date '{{ fecha_corte }}' - 7
        ) as viajes_ultimos_7d,
        count(*) filter (
            where fecha > date '{{ fecha_corte }}' - 30
        ) as viajes_ultimos_30d,
        count(*) filter (
            where fecha > date '{{ fecha_corte }}' - 90
        ) as viajes_ultimos_90d,
        count(*) as viajes_total,

        count(distinct fecha) as dias_activos,
        date '{{ fecha_corte }}' - max(fecha) as dias_desde_ultimo_viaje,
        date '{{ fecha_corte }}' - min(fecha) as dias_desde_primer_viaje,

        count(distinct modo) as cantidad_modos,
        count(*) filter (where modo = 'TRANSMETRO') as viajes_transmetro,
        count(*) filter (where modo = 'TRANSURBANO') as viajes_transurbano,
        count(*) filter (where modo = 'METRORIEL') as viajes_metroriel,
        count(*) filter (where modo = 'AEROMETRO') as viajes_aerometro,

        round(avg(case when en_hora_pico then 1.0 else 0.0 end), 4)
            as proporcion_hora_pico,
        round(avg(case when en_fin_semana then 1.0 else 0.0 end), 4)
            as proporcion_fin_semana,

        count(distinct zona) as zonas_distintas,

        round(sum(monto_gtq), 2) as gasto_total_gtq,
        round(avg(monto_gtq), 2) as gasto_promedio_viaje_gtq

    from viajes
    group by usuario_sk

),

modo_preferido as (

    select distinct on (usuario_sk)
        usuario_sk,
        modo as modo_mas_usado
    from viajes
    group by usuario_sk, modo
    order by usuario_sk, count(*) desc, modo

),

zona_preferida as (

    select distinct on (usuario_sk)
        usuario_sk,
        zona as zona_origen_mas_frecuente
    from viajes
    group by usuario_sk, zona
    order by usuario_sk, count(*) desc, zona

),

rechazos as (

    select
        usuario_sk,
        count(*) as transacciones_rechazadas
    from eventos_usuario
    where not viaje_valido
    group by usuario_sk

),

perfil as (
    select
        usuario.usuario_sk,
        max(historial.perfil) as perfil_padron
    from {{ ref('dim_usuario_conformado') }} usuario

    inner join (
        select distinct on (usuario_natural_id)
            usuario_natural_id,
            perfil
        from {{ ref('dim_usuario_hist') }}
        where valido_desde::date <= date '{{ fecha_corte }}'
        order by
            usuario_natural_id,
            valido_desde desc,
            secuencia desc
    ) historial
        on usuario.modo = 'TRANSMETRO'
       and usuario.usuario_origen_id = historial.usuario_natural_id

    group by usuario.usuario_sk
)

select
    agregado.usuario_sk,
    date '{{ fecha_corte }}' as fecha_corte,
    perfil.perfil_padron,

    agregado.viajes_ultimos_7d,
    agregado.viajes_ultimos_30d,
    agregado.viajes_ultimos_90d,
    agregado.viajes_total,
    agregado.dias_activos,
    agregado.dias_desde_ultimo_viaje,
    agregado.dias_desde_primer_viaje,

    modo_preferido.modo_mas_usado,
    agregado.cantidad_modos,
    agregado.cantidad_modos >= 2 as es_multimodal,
    agregado.viajes_transmetro,
    agregado.viajes_transurbano,
    agregado.viajes_metroriel,
    agregado.viajes_aerometro,

    agregado.proporcion_hora_pico,
    agregado.proporcion_fin_semana,
    zona_preferida.zona_origen_mas_frecuente,
    agregado.zonas_distintas,

    agregado.gasto_total_gtq,
    agregado.gasto_promedio_viaje_gtq,
    coalesce(rechazos.transacciones_rechazadas, 0)
        as transacciones_rechazadas

from agregado

inner join modo_preferido
    on agregado.usuario_sk = modo_preferido.usuario_sk

inner join zona_preferida
    on agregado.usuario_sk = zona_preferida.usuario_sk

left join rechazos
    on agregado.usuario_sk = rechazos.usuario_sk

left join perfil
    on agregado.usuario_sk = perfil.usuario_sk
