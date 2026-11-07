-- Verificar la cantidad de usuarios disponibles en los cortes A, B y C.
SELECT
    cutoff_date,
    COUNT(*) AS total_users,
    COUNT(DISTINCT usuario_sk) AS unique_users
FROM churn.churn_features
WHERE cutoff_date IN (
    '2026-07-01',
    '2026-07-31',
    '2026-08-30'
)
GROUP BY cutoff_date
ORDER BY cutoff_date;

-- Verificar la distribución de las etiquetas de abandono en los cortes disponibles.
SELECT
    cutoff_date,
    COUNT(*) AS total_users,
    COUNT(churn_label) AS labeled_users,
    SUM(CASE WHEN churn_label = 1 THEN 1 ELSE 0 END) AS churn_users,
    ROUND(
        100.0 * SUM(CASE WHEN churn_label = 1 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(churn_label), 0),
        2
    ) AS churn_rate_pct
FROM churn.churn_features
WHERE cutoff_date IN (
    '2026-07-01',
    '2026-07-31',
    '2026-08-30'
)
GROUP BY cutoff_date
ORDER BY cutoff_date;

-- Comprobar que cada usuario aparece una sola vez dentro de cada fecha de corte.
SELECT
    cutoff_date,
    usuario_sk,
    COUNT(*) AS occurrences
FROM churn.churn_features
WHERE cutoff_date IN (
    '2026-07-01',
    '2026-07-31',
    '2026-08-30'
)
GROUP BY cutoff_date, usuario_sk
HAVING COUNT(*) > 1;

-- Identificar registros sin identificador o sin fecha de corte.
SELECT
    COUNT(*) AS total_records,
    COUNT(*) FILTER (
        WHERE usuario_sk IS NULL
    ) AS null_user_ids,
    COUNT(*) FILTER (
        WHERE cutoff_date IS NULL
    ) AS null_cutoff_dates
FROM churn.churn_features;

-- Verificar la población del corte B utilizada para la evaluación temporal.
SELECT
    cutoff_date,
    COUNT(*) AS total_users,
    COUNT(DISTINCT usuario_sk) AS unique_users
FROM churn.churn_features
WHERE cutoff_date = '2026-07-31'
GROUP BY cutoff_date;

-- Consultar una muestra de las características utilizadas para el análisis de usuarios.
SELECT
    usuario_sk,
    cutoff_date,
    days_since_last_trip,
    trips_7d,
    trips_28d,
    active_days_28d,
    total_spending_gtq
FROM churn.churn_features
WHERE cutoff_date = '2026-07-01'
ORDER BY usuario_sk
LIMIT 20;

-- Comprobar el total de usuarios del corte C antes de generar las predicciones.
SELECT
    cutoff_date,
    COUNT(*) AS total_users,
    COUNT(DISTINCT usuario_sk) AS unique_users
FROM churn.churn_features
WHERE cutoff_date = '2026-08-30'
GROUP BY cutoff_date;

-- Identificar usuarios del corte C que tienen una tarjeta válida registrada en el padrón CDC.
SELECT
    COUNT(DISTINCT c.usuario_sk) AS users_with_card
FROM churn.churn_features c
JOIN silver.dim_usuario_conformado d
    ON c.usuario_sk = d.usuario_sk
WHERE c.cutoff_date = '2026-08-30'
  AND d.modo IN ('TRANSMETRO', 'TRANSURBANO')
  AND EXISTS (
      SELECT 1
      FROM silver.stg_cdc_padron p
      WHERE p.tarjeta = d.usuario_origen_id
        AND p.fecha_cambio < DATE '2026-08-31'
  );

-- Calcular usuarios que no cuentan con una tarjeta CDC identificada.
WITH card_users AS (
    SELECT DISTINCT c.usuario_sk
    FROM churn.churn_features c
    JOIN silver.dim_usuario_conformado d
        ON c.usuario_sk = d.usuario_sk
    WHERE c.cutoff_date = '2026-08-30'
      AND d.modo IN ('TRANSMETRO', 'TRANSURBANO')
      AND EXISTS (
          SELECT 1
          FROM silver.stg_cdc_padron p
          WHERE p.tarjeta = d.usuario_origen_id
            AND p.fecha_cambio < DATE '2026-08-31'
      )
)
SELECT
    COUNT(*) AS users_without_card
FROM churn.churn_features c
LEFT JOIN card_users t
    ON c.usuario_sk = t.usuario_sk
WHERE c.cutoff_date = '2026-08-30'
  AND t.usuario_sk IS NULL;