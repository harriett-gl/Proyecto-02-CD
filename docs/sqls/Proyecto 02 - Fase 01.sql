-- EVIDENCIA 01
-- CONEXIÓN Y VERSIÓN DE POSTGRESQL
SELECT
    current_database() AS database_name,
    current_user AS database_user,
    current_schema() AS current_schema,
    version() AS postgresql_version;

-- EVIDENCIA 02
-- ESQUEMAS DISPONIBLES EN LA BASE DE DATOS
SELECT
    schema_name
FROM information_schema.schemata
WHERE schema_name NOT IN (
    'information_schema',
    'pg_catalog'
)
AND schema_name NOT LIKE 'pg_toast%'
ORDER BY schema_name;

-- EVIDENCIA 03
-- TABLAS Y VISTAS POR ESQUEMA
SELECT
    table_schema,
    table_type,
    COUNT(*) AS total_objects
FROM information_schema.tables
WHERE table_schema NOT IN (
    'information_schema',
    'pg_catalog'
)
GROUP BY
    table_schema,
    table_type
ORDER BY
    table_schema,
    table_type;

-- EVIDENCIA 04
-- INVENTARIO DE MODELOS Y OBJETOS DE DATOS
SELECT
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema NOT IN (
    'information_schema',
    'pg_catalog'
)
ORDER BY
    table_schema,
    table_name;

-- EVIDENCIA 05
-- RECONCILIACIÓN DE LAS NUEVE FUENTES DE STAGING
SELECT 'tm_estaciones' AS source_name,
       COUNT(*) AS total_rows
FROM staging.tm_estaciones

UNION ALL

SELECT 'tu_paradas',
       COUNT(*)
FROM staging.tu_paradas

UNION ALL

SELECT 'mr_estaciones',
       COUNT(*)
FROM staging.mr_estaciones

UNION ALL

SELECT 'am_estaciones',
       COUNT(*)
FROM staging.am_estaciones

UNION ALL

SELECT 'transurbano_transacciones',
       COUNT(*)
FROM staging.transurbano_transacciones

UNION ALL

SELECT 'metroriel_viajes_raw',
       COUNT(*)
FROM staging.metroriel_viajes_raw

UNION ALL

SELECT 'cdc_padron_usuarios',
       COUNT(*)
FROM staging.cdc_padron_usuarios

UNION ALL

SELECT 'transmetro_validaciones',
       COUNT(*)
FROM staging.transmetro_validaciones

UNION ALL

SELECT 'aerometro_boardings',
       COUNT(*)
FROM staging.aerometro_boardings;

-- EVIDENCIA 06
-- TOTAL GENERAL DE REGISTROS EN STAGING
WITH source_counts AS (
    SELECT COUNT(*) AS total FROM staging.tm_estaciones
    UNION ALL
    SELECT COUNT(*) FROM staging.tu_paradas
    UNION ALL
    SELECT COUNT(*) FROM staging.mr_estaciones
    UNION ALL
    SELECT COUNT(*) FROM staging.am_estaciones
    UNION ALL
    SELECT COUNT(*) FROM staging.transurbano_transacciones
    UNION ALL
    SELECT COUNT(*) FROM staging.metroriel_viajes_raw
    UNION ALL
    SELECT COUNT(*) FROM staging.cdc_padron_usuarios
    UNION ALL
    SELECT COUNT(*) FROM staging.transmetro_validaciones
    UNION ALL
    SELECT COUNT(*) FROM staging.aerometro_boardings
)
SELECT
    SUM(total) AS total_staging_rows
FROM source_counts;

-- EVIDENCIA 07
-- EXISTENCIA DE LAS TABLAS DE IDENTIDAD DE USUARIOS
SELECT
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'silver'
  AND table_name IN (
      'dim_usuario_conformado',
      'dim_usuario_hist'
  )
ORDER BY table_name;

-- EVIDENCIA 08
-- TOTAL DE USUARIOS CONFORMADOS E HISTORIAL
SELECT
    'dim_usuario_conformado' AS model_name,
    COUNT(*) AS total_rows
FROM silver.dim_usuario_conformado

UNION ALL

SELECT
    'dim_usuario_hist',
    COUNT(*)
FROM silver.dim_usuario_hist;

-- EVIDENCIA 09
-- MODELOS DE ABORDAJES Y VIAJES
SELECT
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_name IN (
    'fct_abordajes',
    'fct_viajes_metroriel'
)
ORDER BY
    table_schema,
    table_name;

-- EVIDENCIA 10
-- TOTAL DE REGISTROS DE ABORDAJES Y VIAJES
SELECT
    'fct_abordajes' AS model_name,
    COUNT(*) AS total_rows
FROM gold.fct_abordajes

UNION ALL

SELECT
    'fct_viajes_metroriel',
    COUNT(*)
FROM gold.fct_viajes_metroriel;

-- EVIDENCIA 11
-- DISTRIBUCIÓN DE USUARIOS POR CORTE TEMPORAL
SELECT
    cut_name,
    cutoff_date,
    COUNT(*) AS total_users,
    COUNT(*) FILTER (WHERE churn_label = 1) AS churn_users,
    COUNT(*) FILTER (WHERE churn_label = 0) AS active_users,
    COUNT(*) FILTER (WHERE churn_label IS NULL) AS unlabeled_users
FROM churn.churn_population_labels
GROUP BY cut_name, cutoff_date
ORDER BY cutoff_date;

-- EVIDENCIA 12
-- PORCENTAJE DE ABANDONO POR CORTE
SELECT
    cut_name,
    cutoff_date,
    COUNT(*) FILTER (WHERE churn_label IS NOT NULL) AS labeled_users,
    COUNT(*) FILTER (WHERE churn_label = 1) AS churn_users,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE churn_label = 1)
        / NULLIF(
            COUNT(*) FILTER (WHERE churn_label IS NOT NULL),
            0
        ),
        2
    ) AS churn_percentage
FROM churn.churn_population_labels
GROUP BY cut_name, cutoff_date
ORDER BY cutoff_date;

-- EVIDENCIA 13
-- VALIDACIÓN DE USUARIOS DUPLICADOS POR CORTE
SELECT
    cut_name,
    cutoff_date,
    usuario_sk,
    COUNT(*) AS repetitions
FROM churn.churn_population_labels
GROUP BY cut_name, cutoff_date, usuario_sk
HAVING COUNT(*) > 1
ORDER BY repetitions DESC;

-- EVIDENCIA 14
-- VALIDACIÓN DE IDENTIFICADORES Y FECHAS NULAS
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE usuario_sk IS NULL) AS null_user_ids,
    COUNT(*) FILTER (WHERE cutoff_date IS NULL) AS null_cutoff_dates,
    COUNT(*) FILTER (WHERE cut_name IS NULL) AS null_cut_names
FROM churn.churn_population_labels;

-- EVIDENCIA 15
-- DISTRIBUCIÓN DE ETIQUETAS DE ABANDONO
SELECT
    cut_name,
    cutoff_date,
    churn_label,
    COUNT(*) AS total_users
FROM churn.churn_population_labels
GROUP BY cut_name, cutoff_date, churn_label
ORDER BY cutoff_date, churn_label NULLS LAST;

-- EVIDENCIA 16
-- TOTAL DE CARACTERÍSTICAS POR CORTE
SELECT
    cut_name,
    cutoff_date,
    COUNT(*) AS total_feature_rows,
    COUNT(DISTINCT usuario_sk) AS unique_users
FROM churn.churn_features
GROUP BY cut_name, cutoff_date
ORDER BY cutoff_date;

-- EVIDENCIA 17
-- COMPARACIÓN ENTRE POBLACIÓN Y CARACTERÍSTICAS
WITH population AS (
    SELECT
        cut_name,
        cutoff_date,
        COUNT(*) AS population_rows
    FROM churn.churn_population_labels
    GROUP BY cut_name, cutoff_date
),
features AS (
    SELECT
        cut_name,
        cutoff_date,
        COUNT(*) AS feature_rows
    FROM churn.churn_features
    GROUP BY cut_name, cutoff_date
)
SELECT
    p.cut_name,
    p.cutoff_date,
    p.population_rows,
    COALESCE(f.feature_rows, 0) AS feature_rows,
    p.population_rows - COALESCE(f.feature_rows, 0) AS difference
FROM population p
LEFT JOIN features f
    ON p.cut_name = f.cut_name
   AND p.cutoff_date = f.cutoff_date
ORDER BY p.cutoff_date;

-- EVIDENCIA 18
-- INVENTARIO DE CARACTERÍSTICAS PARA MACHINE LEARNING
SELECT
    ordinal_position,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'churn'
  AND table_name = 'churn_features'
ORDER BY ordinal_position;

-- EVIDENCIA 19
-- VALIDACIÓN DE DUPLICADOS EN CARACTERÍSTICAS
SELECT
    cut_name,
    cutoff_date,
    usuario_sk,
    COUNT(*) AS repetitions
FROM churn.churn_features
GROUP BY cut_name, cutoff_date, usuario_sk
HAVING COUNT(*) > 1;

-- EVIDENCIA 20
-- COINCIDENCIA ENTRE CARACTERÍSTICAS Y ETIQUETAS
SELECT
    COUNT(*) AS unmatched_feature_rows
FROM churn.churn_features f
LEFT JOIN churn.churn_population_labels p
    ON f.cut_name = p.cut_name
   AND f.cutoff_date = p.cutoff_date
   AND f.usuario_sk = p.usuario_sk
WHERE p.usuario_sk IS NULL;

-- EVIDENCIA 21
-- VERIFICACIÓN DE LOS TRES CORTES TEMPORALES
SELECT
    MIN(cutoff_date) AS first_cutoff,
    MAX(cutoff_date) AS last_cutoff,
    COUNT(DISTINCT cut_name) AS total_cuts,
    COUNT(*) AS total_rows
FROM churn.churn_population_labels;

-- EVIDENCIA 22
-- VALIDACIÓN DEL CORTE C SIN ETIQUETAS
SELECT
    cut_name,
    cutoff_date,
    COUNT(*) AS total_users,
    COUNT(*) FILTER (
        WHERE churn_label IS NOT NULL
    ) AS incorrectly_labeled_users
FROM churn.churn_population_labels
WHERE cut_name = 'C'
GROUP BY cut_name, cutoff_date;

-- EVIDENCIA 23
-- VALIDACIÓN DE ETIQUETAS EN LOS CORTES A Y B
SELECT
    cut_name,
    cutoff_date,
    COUNT(*) AS total_users,
    COUNT(*) FILTER (
        WHERE churn_label IS NULL
    ) AS missing_labels
FROM churn.churn_population_labels
WHERE cut_name IN ('A', 'B')
GROUP BY cut_name, cutoff_date
ORDER BY cutoff_date;


-- EVIDENCIA 24
-- RESUMEN GENERAL DE LA POBLACIÓN
SELECT
    COUNT(*) AS total_population_rows,
    COUNT(DISTINCT usuario_sk) AS unique_users_across_cuts,
    COUNT(DISTINCT cut_name) AS total_cuts,
    COUNT(*) FILTER (
        WHERE churn_label = 1
    ) AS total_positive_labels,
    COUNT(*) FILTER (
        WHERE churn_label = 0
    ) AS total_negative_labels,
    COUNT(*) FILTER (
        WHERE churn_label IS NULL
    ) AS total_unlabeled_rows
FROM churn.churn_population_labels;

-- EVIDENCIA 25
-- CONTROL FINAL DE CALIDAD DE DATOS
WITH duplicate_check AS (
    SELECT COUNT(*) AS duplicate_groups
    FROM (
        SELECT cut_name, cutoff_date, usuario_sk
        FROM churn.churn_population_labels
        GROUP BY cut_name, cutoff_date, usuario_sk
        HAVING COUNT(*) > 1
    ) d
),
null_check AS (
    SELECT
        COUNT(*) FILTER (
            WHERE usuario_sk IS NULL
               OR cutoff_date IS NULL
               OR cut_name IS NULL
        ) AS invalid_rows
    FROM churn.churn_population_labels
),
unmatched_check AS (
    SELECT COUNT(*) AS unmatched_rows
    FROM churn.churn_features f
    LEFT JOIN churn.churn_population_labels p
        ON f.cut_name = p.cut_name
       AND f.cutoff_date = p.cutoff_date
       AND f.usuario_sk = p.usuario_sk
    WHERE p.usuario_sk IS NULL
)
SELECT
    d.duplicate_groups,
    n.invalid_rows,
    u.unmatched_rows,
    CASE
        WHEN d.duplicate_groups = 0
         AND n.invalid_rows = 0
         AND u.unmatched_rows = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS quality_status
FROM duplicate_check d
CROSS JOIN null_check n
CROSS JOIN unmatched_check u;

-- EVIDENCIA 26
-- Verificar la distribución de usuarios por corte temporal
SELECT
    cut_name,
    cutoff_date,
    COUNT(*) AS total_users,
    COUNT(*) FILTER (WHERE churn_label = 1) AS churn_users,
    COUNT(*) FILTER (WHERE churn_label = 0) AS active_users,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE churn_label = 1)
        / NULLIF(COUNT(churn_label), 0),
        2
    ) AS churn_percentage
FROM churn.churn_population_labels
GROUP BY cut_name, cutoff_date
ORDER BY cutoff_date;


-- EVIDENCIA 27
-- Comprobar la correspondencia entre población y características
WITH population AS (
    SELECT
        cut_name,
        COUNT(*) AS population_rows
    FROM churn.churn_population_labels
    GROUP BY cut_name
),
features AS (
    SELECT
        cut_name,
        COUNT(*) AS feature_rows
    FROM churn.churn_features
    GROUP BY cut_name
)
SELECT
    p.cut_name,
    p.population_rows,
    f.feature_rows,
    p.population_rows - COALESCE(f.feature_rows, 0)
        AS row_difference
FROM population p
LEFT JOIN features f
    ON p.cut_name = f.cut_name
ORDER BY p.cut_name;


-- EVIDENCIA 28
-- Verificar las etiquetas de abandono en cada corte
SELECT
    cut_name,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE churn_label = 0)
        AS active_labels,
    COUNT(*) FILTER (WHERE churn_label = 1)
        AS churn_labels,
    COUNT(*) FILTER (WHERE churn_label IS NULL)
        AS null_labels
FROM churn.churn_population_labels
GROUP BY cut_name
ORDER BY cut_name;


-- EVIDENCIA 29
-- Comprobar que no existan usuarios duplicados por corte
SELECT
    cut_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT usuario_sk) AS unique_users,
    COUNT(*) - COUNT(DISTINCT usuario_sk)
        AS duplicate_rows
FROM churn.churn_population_labels
GROUP BY cut_name
ORDER BY cut_name;


-- EVIDENCIA 30
-- Consultar las columnas del modelo de características
SELECT
    ordinal_position,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'churn'
  AND table_name = 'churn_features'
ORDER BY ordinal_position;


-- EVIDENCIA 31
-- Verificar la integridad de las características predictivas
SELECT
    cut_name,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE usuario_sk IS NULL
           OR cutoff_date IS NULL
           OR cut_name IS NULL
    ) AS invalid_identifiers,
    COUNT(*) FILTER (
        WHERE trips_28d IS NULL
           OR trips_7d IS NULL
           OR active_days_28d IS NULL
           OR days_since_last_trip IS NULL
    ) AS missing_core_features
FROM churn.churn_features
GROUP BY cut_name
ORDER BY cut_name;


-- EVIDENCIA 32
-- Verificar que las características tengan población asociada
SELECT
    f.cut_name,
    COUNT(*) AS total_features,
    COUNT(*) FILTER (
        WHERE p.usuario_sk IS NULL
    ) AS unmatched_features
FROM churn.churn_features f
LEFT JOIN churn.churn_population_labels p
    ON f.cut_name = p.cut_name
   AND f.cutoff_date = p.cutoff_date
   AND f.usuario_sk = p.usuario_sk
GROUP BY f.cut_name
ORDER BY f.cut_name;


-- EVIDENCIA 33
-- Resumen final de calidad de población y características
WITH population_quality AS (
    SELECT
        COUNT(*) AS population_rows,
        COUNT(*) FILTER (
            WHERE usuario_sk IS NULL
               OR cutoff_date IS NULL
               OR cut_name IS NULL
        ) AS invalid_rows,
        COUNT(*) - COUNT(DISTINCT (
            cut_name, cutoff_date, usuario_sk
        )) AS duplicate_rows
    FROM churn.churn_population_labels
),
feature_quality AS (
    SELECT
        COUNT(*) AS feature_rows
    FROM churn.churn_features
)
SELECT
    p.population_rows,
    f.feature_rows,
    p.invalid_rows,
    p.duplicate_rows,
    CASE
        WHEN p.population_rows = f.feature_rows
         AND p.invalid_rows = 0
         AND p.duplicate_rows = 0
        THEN 'PASS'
        ELSE 'REVIEW'
    END AS quality_status
FROM population_quality p
CROSS JOIN feature_quality f;