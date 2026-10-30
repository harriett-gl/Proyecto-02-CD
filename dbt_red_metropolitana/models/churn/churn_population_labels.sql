{{ config(materialized='table', schema='churn') }}

-- Definir los cortes temporales del proyecto
WITH cuts AS (
    SELECT DATE '2026-07-01' AS cutoff_date, 'A' AS cut_name, TRUE AS has_label
    UNION ALL
    SELECT DATE '2026-07-31', 'B', TRUE
    UNION ALL
    SELECT DATE '2026-08-30', 'C', FALSE
),

-- Unificar los abordajes válidos de los cuatro medios
valid_trips AS (
    SELECT
        usuario_sk,
        transport_mode,
        trip_timestamp,
        amount_gtq
    FROM {{ ref('churn_valid_trips') }}
),

-- Identificar usuarios con al menos dos viajes en los 28 días previos
eligible_users AS (
    SELECT
        cuts.cut_name,
        cuts.cutoff_date,
        cuts.has_label,
        trips.usuario_sk,
        COUNT(*) AS trips_previous_28d
    FROM cuts
    INNER JOIN valid_trips trips
        ON trips.trip_timestamp >=
           (cuts.cutoff_date - INTERVAL '28 days')::timestamp AT TIME ZONE 'America/Guatemala'
       AND trips.trip_timestamp <
           cuts.cutoff_date::timestamp AT TIME ZONE 'America/Guatemala'
    GROUP BY
        cuts.cut_name,
        cuts.cutoff_date,
        cuts.has_label,
        trips.usuario_sk
    HAVING COUNT(*) >= 2
),

-- Identificar usuarios de Transmetro con baja CDC antes del corte
deleted_users AS (
    SELECT DISTINCT
        cuts.cut_name,
        usuario.usuario_sk
    FROM cuts
    INNER JOIN {{ ref('dim_usuario_conformado') }} usuario
        ON usuario.modo = 'TRANSMETRO'
    INNER JOIN {{ ref('dim_usuario_hist') }} historial
        ON usuario.usuario_origen_id = historial.usuario_natural_id
    WHERE historial.operacion_origen = 'DELETE'
      AND historial.valido_desde < cuts.cutoff_date
),

-- Contabilizar viajes durante los 30 días posteriores al corte
future_trips AS (
    SELECT
        eligible.cut_name,
        eligible.usuario_sk,
        COUNT(trips.usuario_sk) AS trips_next_30d
    FROM eligible_users eligible
    LEFT JOIN valid_trips trips
        ON eligible.usuario_sk = trips.usuario_sk
       AND trips.trip_timestamp >=
           eligible.cutoff_date::timestamp AT TIME ZONE 'America/Guatemala'
       AND trips.trip_timestamp <
           (eligible.cutoff_date + INTERVAL '30 days')::timestamp AT TIME ZONE 'America/Guatemala'
    GROUP BY
        eligible.cut_name,
        eligible.usuario_sk
)

-- Generar la población y la etiqueta de abandono
SELECT
    eligible.cut_name,
    eligible.cutoff_date,
    eligible.usuario_sk,
    eligible.trips_previous_28d,
    CASE
        WHEN eligible.has_label = FALSE THEN NULL
        WHEN future.trips_next_30d = 0 THEN 1
        ELSE 0
    END AS churn_label
FROM eligible_users eligible
INNER JOIN future_trips future
    ON eligible.cut_name = future.cut_name
   AND eligible.usuario_sk = future.usuario_sk
LEFT JOIN deleted_users deleted
    ON eligible.cut_name = deleted.cut_name
   AND eligible.usuario_sk = deleted.usuario_sk
WHERE deleted.usuario_sk IS NULL
