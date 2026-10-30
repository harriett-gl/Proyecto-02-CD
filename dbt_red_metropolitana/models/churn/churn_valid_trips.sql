
{{ config(materialized='view', schema='churn') }}

-- Construir eventos válidos directamente desde Silver
-- Mantener la misma interpretación temporal del modelo original

WITH silver_abordajes AS (

    -- Transmetro
    SELECT
        'TRANSMETRO' AS transport_mode,
        usuario_origen_id,
        fecha_hora_local AS trip_timestamp,
        monto_gtq AS amount_gtq
    FROM {{ ref('transmetro_validaciones') }}

    UNION ALL

    -- Transurbano
    SELECT
        'TRANSURBANO',
        usuario_origen_id,
        fecha_hora_local,
        monto_gtq
    FROM {{ ref('transurbano_transacciones') }}
    WHERE transaccion_aprobada = TRUE

    UNION ALL

    -- Aerómetro
    SELECT
        'AEROMETRO',
        usuario_origen_id,
        fecha_hora_local,
        monto_gtq
    FROM {{ ref('aerometro_boardings') }}

),

silver_metroriel AS (

    -- MetroRiel
    SELECT
        'METRORIEL' AS transport_mode,
        usuario_origen_id,
        fecha_hora_entrada AT TIME ZONE 'America/Guatemala'
            AS trip_timestamp,
        monto_gtq AS amount_gtq
    FROM {{ ref('metroriel_viajes') }}

),

silver_events AS (

    SELECT
        transport_mode,
        usuario_origen_id,
        trip_timestamp,
        amount_gtq
    FROM silver_abordajes

    UNION ALL

    SELECT
        transport_mode,
        usuario_origen_id,
        trip_timestamp,
        amount_gtq
    FROM silver_metroriel

)

-- Relacionar los viajes con los usuarios conformados
SELECT
    usuario.usuario_sk,
    eventos.transport_mode,
    eventos.trip_timestamp,
    eventos.amount_gtq

FROM silver_events eventos

INNER JOIN {{ ref('dim_usuario_conformado') }} usuario
    ON eventos.transport_mode = usuario.modo
   AND eventos.usuario_origen_id = usuario.usuario_origen_id

WHERE usuario.usuario_sk IS NOT NULL
