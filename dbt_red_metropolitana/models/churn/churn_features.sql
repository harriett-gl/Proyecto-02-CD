{{ config(materialized='table', schema='churn') }}

-- Obtener la población elegible de cada corte
WITH population AS (
    SELECT
        cut_name,
        cutoff_date,
        usuario_sk,
        churn_label
    FROM {{ ref('churn_population_labels') }}
),

-- Unificar viajes válidos de los cuatro medios
valid_trips AS (
    SELECT
        usuario_sk,
        transport_mode,
        trip_timestamp,
        amount_gtq
    FROM {{ ref('churn_valid_trips') }}
),

-- Restringir viajes al periodo histórico completo
historical_trips AS (
    SELECT
        population.cut_name,
        population.cutoff_date,
        population.usuario_sk,
        trips.transport_mode,
        trips.trip_timestamp,
        trips.amount_gtq,
        (trips.trip_timestamp AT TIME ZONE 'America/Guatemala')::date AS trip_date,
        EXTRACT(
            HOUR FROM trips.trip_timestamp AT TIME ZONE 'America/Guatemala'
        ) AS trip_hour,
        EXTRACT(
            ISODOW FROM trips.trip_timestamp AT TIME ZONE 'America/Guatemala'
        ) AS weekday_number
    FROM valid_trips trips
    INNER JOIN population
        ON trips.usuario_sk = population.usuario_sk
       AND trips.trip_timestamp >=
           (population.cutoff_date - INTERVAL '28 days')::timestamp AT TIME ZONE 'America/Guatemala'
       AND trips.trip_timestamp <
           population.cutoff_date::timestamp AT TIME ZONE 'America/Guatemala'
),

-- Agrupar viajes por usuario, corte, fecha y modo
daily_trips AS (
    SELECT
        cut_name,
        cutoff_date,
        usuario_sk,
        trip_date,
        transport_mode,
        COUNT(*) AS trip_count,
        COUNT(*) FILTER (
            WHERE trip_timestamp >=
                (cutoff_date - INTERVAL '7 days')::timestamp AT TIME ZONE 'America/Guatemala'
        ) AS recent_trip_count,
        SUM(COALESCE(amount_gtq, 0)) AS daily_spending,
        COUNT(*) FILTER (
            WHERE weekday_number IN (6, 7)
        ) AS weekend_count,
        COUNT(*) FILTER (
            WHERE trip_hour BETWEEN 6 AND 9
               OR trip_hour BETWEEN 16 AND 19
        ) AS peak_hour_count
    FROM historical_trips
    GROUP BY
        cut_name,
        cutoff_date,
        usuario_sk,
        trip_date,
        transport_mode
),

-- Calcular características de movilidad
aggregated_features AS (
    SELECT
        cut_name,
        cutoff_date,
        usuario_sk,

        SUM(trip_count) AS trips_28d,
        SUM(recent_trip_count) AS trips_7d,
        COUNT(DISTINCT trip_date) AS active_days_28d,
        cutoff_date - MAX(trip_date) AS days_since_last_trip,

        COUNT(DISTINCT transport_mode) AS transport_modes_count,

        SUM(trip_count) FILTER (
            WHERE transport_mode = 'TRANSMETRO'
        ) AS transmetro_trips,

        SUM(trip_count) FILTER (
            WHERE transport_mode = 'TRANSURBANO'
        ) AS transurbano_trips,

        SUM(trip_count) FILTER (
            WHERE transport_mode = 'METRORIEL'
        ) AS metroriel_trips,

        SUM(trip_count) FILTER (
            WHERE transport_mode = 'AEROMETRO'
        ) AS aerometro_trips,

        ROUND(
            SUM(weekend_count)::numeric /
            NULLIF(SUM(trip_count), 0),
            4
        ) AS weekend_trip_ratio,

        ROUND(
            SUM(peak_hour_count)::numeric /
            NULLIF(SUM(trip_count), 0),
            4
        ) AS peak_hour_trip_ratio,

        ROUND(SUM(daily_spending), 2) AS total_spending_gtq,

        ROUND(
            SUM(daily_spending) /
            NULLIF(SUM(trip_count), 0),
            2
        ) AS average_spending_gtq

    FROM daily_trips
    GROUP BY cut_name, cutoff_date, usuario_sk
)

-- Generar características y etiquetas
SELECT
    population.cut_name,
    population.cutoff_date,
    population.usuario_sk,

    features.trips_28d,
    features.trips_7d,
    features.active_days_28d,
    features.days_since_last_trip,

    features.transport_modes_count,
    features.transport_modes_count >= 2 AS is_multimodal,

    COALESCE(features.transmetro_trips, 0) AS transmetro_trips,
    COALESCE(features.transurbano_trips, 0) AS transurbano_trips,
    COALESCE(features.metroriel_trips, 0) AS metroriel_trips,
    COALESCE(features.aerometro_trips, 0) AS aerometro_trips,

    features.weekend_trip_ratio,
    features.peak_hour_trip_ratio,
    features.total_spending_gtq,
    features.average_spending_gtq,

    population.churn_label

FROM population
INNER JOIN aggregated_features features
    ON population.cut_name = features.cut_name
   AND population.usuario_sk = features.usuario_sk
