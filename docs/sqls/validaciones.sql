-- VALIDACIONES GENERALES - PROYECTO RED METROPOLITANA
-- FASE 01


-- 1. CREACIÓN DE ESQUEMAS
-- Ejecutar únicamente durante la configuración inicial.
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS quarantine;
CREATE SCHEMA IF NOT EXISTS audit;


-- 2. VALIDACIÓN DE ESQUEMAS CREADOS
SELECT schema_name AS esquema
FROM information_schema.schemata
WHERE schema_name IN (
    'staging',
    'silver',
    'gold',
    'quarantine',
    'audit'
)
ORDER BY schema_name;


-- 3. CONTEO DE REGISTROS EN STAGING
-- Ejecutar después de cargar Staging y antes de vaciarlo.
SELECT 'tm_estaciones' AS tabla, COUNT(*) AS registros
FROM staging.tm_estaciones

UNION ALL

SELECT 'tu_paradas', COUNT(*)
FROM staging.tu_paradas

UNION ALL

SELECT 'mr_estaciones', COUNT(*)
FROM staging.mr_estaciones

UNION ALL

SELECT 'am_estaciones', COUNT(*)
FROM staging.am_estaciones

UNION ALL

SELECT 'transmetro_validaciones', COUNT(*)
FROM staging.transmetro_validaciones

UNION ALL

SELECT 'transurbano_transacciones', COUNT(*)
FROM staging.transurbano_transacciones

UNION ALL

SELECT 'metroriel_viajes_raw', COUNT(*)
FROM staging.metroriel_viajes_raw

UNION ALL

SELECT 'aerometro_boardings', COUNT(*)
FROM staging.aerometro_boardings

UNION ALL

SELECT 'cdc_padron_usuarios', COUNT(*)
FROM staging.cdc_padron_usuarios

ORDER BY tabla;


-- 4. ESTADO FINAL DEL PADRÓN CDC DE TRANSMETRO
SELECT
    (SELECT COUNT(*)
     FROM staging.metroriel_viajes_raw)
        AS registros_originales,

    (SELECT COUNT(*)
     FROM silver.metroriel_viajes)
        AS registros_silver,

    (SELECT COUNT(*)
     FROM quarantine.metroriel_sin_salida)
        AS viajes_sin_salida;

--5. ESTADO FINAL DEL PADRÓN CDC DE TRANSMETRO
SELECT
    COUNT(*) AS total_tarjetas,
    COUNT(*) FILTER (WHERE activo = true) AS tarjetas_activas,
    COUNT(*) FILTER (WHERE activo = false) AS tarjetas_inactivas
FROM silver.dim_usuario_actual;


-- 6. CATÁLOGO MÍNIMO DE USUARIOS DE METRORIEL
SELECT COUNT(*) AS usuarios_unicos_metroriel
FROM silver.cat_usuario_metroriel;


-- 7. USUARIOS ÚNICOS POR OPERADOR
SELECT
    'Transurbano' AS operador,
    COUNT(*) AS usuarios_unicos
FROM silver.cat_usuario_transurbano

UNION ALL

SELECT
    'MetroRiel',
    COUNT(*)
FROM silver.cat_usuario_metroriel

UNION ALL

SELECT
    'Aerometro',
    COUNT(*)
FROM silver.cat_usuario_aerometro

ORDER BY operador;


-- 8. USUARIOS EN LA DIMENSIÓN CONFORMADA POR MODO
SELECT
    modo,
    COUNT(*) AS usuarios
FROM silver.dim_usuario_conformado
GROUP BY modo
ORDER BY modo;


-- 9. VALIDACIÓN DE CONEXIÓN A POSTGRESQL
SELECT
    current_user AS usuario_conectado,
    current_database() AS base_de_datos;

-- 10. OPERACIONES CDC PROCESADAS
SELECT
    op AS operacion,
    COUNT(*) AS cantidad
FROM staging.cdc_padron_usuarios
GROUP BY op
ORDER BY op;

-- 11. TARJETAS ACTIVAS E INACTIVAS
SELECT
    COUNT(*) AS total_tarjetas,
    COUNT(*) FILTER (WHERE activo = true) AS activas,
    COUNT(*) FILTER (WHERE activo = false) AS inactivas
FROM silver.dim_usuario_actual;

-- 12. CONTEO DE CUARENTENA POR TABLA
SELECT 'cdc_llaves_invalidas' AS tabla, COUNT(*) AS cantidad
FROM quarantine.cdc_llaves_invalidas

UNION ALL

SELECT 'metroriel_sin_salida', COUNT(*)
FROM quarantine.metroriel_sin_salida

UNION ALL

SELECT 'transmetro_duplicados', COUNT(*)
FROM quarantine.transmetro_duplicados

UNION ALL

SELECT 'transurbano_invalidos', COUNT(*)
FROM quarantine.transurbano_invalidos

UNION ALL

SELECT 'aerometro_invalidos', COUNT(*)
FROM quarantine.aerometro_invalidos

ORDER BY tabla;

-- 12. CUARENTENA POR MOTIVO DE RECHAZO
SELECT
    'cdc_llaves_invalidas' AS tabla,
    motivo_rechazo AS motivo,
    COUNT(*) AS cantidad
FROM quarantine.cdc_llaves_invalidas
GROUP BY motivo_rechazo

UNION ALL

SELECT
    'metroriel_sin_salida' AS tabla,
    motivo_rechazo AS motivo,
    COUNT(*) AS cantidad
FROM quarantine.metroriel_sin_salida
GROUP BY motivo_rechazo

UNION ALL

SELECT
    'transmetro_duplicados' AS tabla,
    motivo_rechazo AS motivo,
    COUNT(*) AS cantidad
FROM quarantine.transmetro_duplicados
GROUP BY motivo_rechazo

UNION ALL

SELECT
    'transurbano_invalidos' AS tabla,
    motivo_rechazo AS motivo,
    COUNT(*) AS cantidad
FROM quarantine.transurbano_invalidos
GROUP BY motivo_rechazo

UNION ALL

SELECT
    'aerometro_invalidos' AS tabla,
    motivo_rechazo AS motivo,
    COUNT(*) AS cantidad
FROM quarantine.aerometro_invalidos
GROUP BY motivo_rechazo

ORDER BY tabla, motivo;


-- 13. CONTEOS DEL MODELO DIMENSIONAL GOLD
SELECT
    'fct_abordajes' AS tabla,
    COUNT(*) AS cantidad
FROM gold.fct_abordajes

UNION ALL

SELECT
    'fct_viajes_metroriel' AS tabla,
    COUNT(*) AS cantidad
FROM gold.fct_viajes_metroriel

UNION ALL

SELECT
    'dim_usuario' AS tabla,
    COUNT(*) AS cantidad
FROM gold.dim_usuario

UNION ALL

SELECT
    'dim_fecha' AS tabla,
    COUNT(*) AS cantidad
FROM gold.dim_fecha

UNION ALL

SELECT
    'dim_hora' AS tabla,
    COUNT(*) AS cantidad
FROM gold.dim_hora

UNION ALL

SELECT
    'dim_modo' AS tabla,
    COUNT(*) AS cantidad
FROM gold.dim_modo

UNION ALL

SELECT
    'dim_zona' AS tabla,
    COUNT(*) AS cantidad
FROM gold.dim_zona

ORDER BY tabla;

-- 14. ÚLTIMAS DOS EJECUCIONES DEL PIPELINE
SELECT
    fecha_inicio,
    estado,
    registros_staging,
    registros_silver,
    registros_gold,
    registros_cuarentena,
    duracion_segundos
FROM audit.ejecuciones_pipeline
ORDER BY fecha_inicio DESC
LIMIT 2;