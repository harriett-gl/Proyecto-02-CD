{{ config(materialized='view') }}

/*
    DEMANDA DE LA RED POR MODO, ZONA, FECHA Y HORA  (tablero 2.1)

    Grano: modo x zona x fecha x hora.
    Une los abordajes (Transmetro, Transurbano, Aerómetro) con las entradas
    de MetroRiel para poder comparar los CUATRO modos en un mismo gráfico.
    Un viaje de MetroRiel cuenta como un abordaje en su estación de entrada
    (definición oficial en docs/gobernanza.md).
*/

with eventos as (

    select
        modo_sk,
        modo_nombre,
        zona_sk,
        zona_nombre,
        fecha_sk,
        hora_sk,
        cantidad_abordajes,
        monto_gtq
    from {{ ref('fct_abordajes') }}

    union all

    select
        modo_sk,
        modo_nombre,
        zona_entrada_sk,
        zona_entrada,
        fecha_sk,
        hora_entrada_sk,
        cantidad_viajes,
        monto_gtq
    from {{ ref('fct_viajes_metroriel') }}

)

select
    eventos.modo_sk,
    eventos.modo_nombre,
    eventos.zona_sk,
    eventos.zona_nombre,
    eventos.fecha_sk,
    eventos.hora_sk,
    hora.franja_horaria,
    hora.es_hora_pico,
    fecha.es_dia_habil,
    sum(eventos.cantidad_abordajes) as abordajes,
    sum(eventos.monto_gtq) as ingreso_gtq

from eventos

inner join {{ ref('dim_hora') }} hora
    on eventos.hora_sk = hora.hora_sk

inner join {{ ref('dim_fecha') }} fecha
    on eventos.fecha_sk = fecha.fecha_sk

group by 1, 2, 3, 4, 5, 6, 7, 8, 9
