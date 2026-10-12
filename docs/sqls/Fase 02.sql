/* Mostrar todas las tablas existentes dentro del esquema Gold */
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'gold'
ORDER BY table_name;

/* Mostrar las tablas existentes en Staging, Silver, Gold y Quarantine */
SELECT
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema IN ('staging', 'silver', 'gold', 'quarantine')
ORDER BY table_schema, table_name;

/* Mostrar todas las tablas de Silver para verificar los datos transformados de la Fase 01 */
SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = 'silver'
ORDER BY table_name;

/* Contar la cantidad total de registros de la tabla de hechos de abordajes */
SELECT COUNT(*) AS total_abordajes
FROM gold.fct_abordajes;

/* Contar la cantidad total de registros de viajes de MetroRiel */
SELECT COUNT(*) AS total_viajes_metroriel
FROM gold.fct_viajes_metroriel;

/* Contar los usuarios de Transurbano disponibles en la capa Silver */
SELECT COUNT(*) AS total_usuarios_transurbano
FROM silver.cat_usuario_transurbano;

/* Mostrar todas las tablas disponibles actualmente en la capa Staging */
SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = 'staging'
ORDER BY table_name;

/* Verificar la cantidad de registros almacenados en cada tabla de Staging */
SELECT 'tm_estaciones' AS tabla, COUNT(*) AS registros
FROM staging.tm_estaciones

UNION ALL

SELECT 'tu_paradas' AS tabla, COUNT(*) AS registros
FROM staging.tu_paradas

UNION ALL

SELECT 'mr_estaciones' AS tabla, COUNT(*) AS registros
FROM staging.mr_estaciones

UNION ALL

SELECT 'am_estaciones' AS tabla, COUNT(*) AS registros
FROM staging.am_estaciones

UNION ALL

SELECT 'transmetro_validaciones' AS tabla, COUNT(*) AS registros
FROM staging.transmetro_validaciones

UNION ALL

SELECT 'transurbano_transacciones' AS tabla, COUNT(*) AS registros
FROM staging.transurbano_transacciones

UNION ALL

SELECT 'metroriel_viajes_raw' AS tabla, COUNT(*) AS registros
FROM staging.metroriel_viajes_raw

UNION ALL

SELECT 'aerometro_boardings' AS tabla, COUNT(*) AS registros
FROM staging.aerometro_boardings

UNION ALL

SELECT 'cdc_padron_usuarios' AS tabla, COUNT(*) AS registros
FROM staging.cdc_padron_usuarios

ORDER BY tabla;

/* Verificar que las tablas de hechos de Gold contienen datos para el tablero de Tableau */
SELECT 'fct_abordajes' AS tabla, COUNT(*) AS registros
FROM gold.fct_abordajes

UNION ALL

SELECT 'fct_viajes_metroriel', COUNT(*)
FROM gold.fct_viajes_metroriel

ORDER BY tabla;

/* Mostrar las columnas disponibles en la tabla de hechos de abordajes */
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'gold'
  AND table_name = 'fct_abordajes'
ORDER BY ordinal_position;

/* Mostrar las columnas disponibles en la tabla de hechos de viajes de MetroRiel */
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'gold'
  AND table_name = 'fct_viajes_metroriel'
ORDER BY ordinal_position;

/* Mostrar las columnas disponibles en la tabla de hechos de viajes de MetroRiel */
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'gold'
  AND table_name = 'fct_viajes_metroriel'
ORDER BY ordinal_position;

/* Mostrar las columnas disponibles en la dimensión de tiempo */
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'gold'
  AND table_name = 'dim_hora'
ORDER BY ordinal_position;

/* Mostrar los modos de transporte disponibles en Gold */
SELECT *
FROM gold.dim_modo
ORDER BY modo_sk;

SELECT
    cantidad_modos,
    COUNT(*) AS cantidad_usuarios
FROM features.features_usuario_movilidad
GROUP BY cantidad_modos
ORDER BY cantidad_modos;

SELECT
    COUNT(*) AS usuarios_multimodales
FROM features.features_usuario_movilidad
WHERE cantidad_modos >= 2;

/* 1. Usuarios distintos por modo */
SELECT
    modo,
    COUNT(DISTINCT usuario_id) AS usuarios
FROM (
    SELECT
        usuario_origen_id AS usuario_id,
        'TRANSMETRO' AS modo
    FROM silver.transmetro_validaciones

    UNION ALL

    SELECT
        usuario_origen_id AS usuario_id,
        'METRORIEL' AS modo
    FROM silver.metroriel_viajes
) t
GROUP BY modo
ORDER BY modo;


/* 2. Buscar usuarios que aparecen en ambos sistemas */
SELECT COUNT(*) AS usuarios_en_ambos
FROM (
    SELECT usuario_origen_id
    FROM silver.transmetro_validaciones

    INTERSECT

    SELECT usuario_origen_id
    FROM silver.metroriel_viajes
) t;


/* 3. Revisar ejemplos de IDs de Transmetro */
SELECT DISTINCT usuario_origen_id
FROM silver.transmetro_validaciones
WHERE usuario_origen_id IS NOT NULL
LIMIT 10;


/* 4. Revisar ejemplos de IDs de MetroRiel */
SELECT DISTINCT usuario_origen_id
FROM silver.metroriel_viajes
WHERE usuario_origen_id IS NOT NULL
LIMIT 10;

/* VERIFICACIÓN DE IDENTIDAD CONFORMADA DE USUARIOS */

/* 1. Ver estructura de silver.dim_usuario_conformado */
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'silver'
  AND table_name = 'dim_usuario_conformado'
ORDER BY ordinal_position;


/* 2. Ver primeros registros de la dimensión conformada */
SELECT *
FROM silver.dim_usuario_conformado
LIMIT 10;


/* 3. Cantidad total de registros */
SELECT
    COUNT(*) AS total_registros
FROM silver.dim_usuario_conformado;


/* 4. Ver estructura de gold.dim_usuario */
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'gold'
  AND table_name = 'dim_usuario'
ORDER BY ordinal_position;


/* 5. Ver primeros registros de Gold */
SELECT *
FROM gold.dim_usuario
LIMIT 10;


/* 6. Cantidad de usuarios en Gold */
SELECT
    COUNT(*) AS total_usuarios_gold
FROM gold.dim_usuario;

/* VALIDACIÓN FINAL DE USUARIOS MULTIMODALES */

/* 1. Distribución de usuarios según cantidad de modos */
SELECT
    cantidad_modos_identificados,
    COUNT(*) AS cantidad_usuarios
FROM gold.dim_usuario
GROUP BY cantidad_modos_identificados
ORDER BY cantidad_modos_identificados;


/* 2. Cantidad real de usuarios multimodales */
SELECT
    COUNT(*) AS usuarios_multimodales
FROM gold.dim_usuario
WHERE cantidad_modos_identificados >= 2;


/* 3. Ver ejemplos de usuarios multimodales */
SELECT
    usuario_sk,
    perfil,
    zona_residencia,
    modos_identificados,
    cantidad_modos_identificados
FROM gold.dim_usuario
WHERE cantidad_modos_identificados >= 2
ORDER BY cantidad_modos_identificados DESC
LIMIT 20;


/* 4. Distribución por combinación de modos */
SELECT
    modos_identificados,
    COUNT(*) AS cantidad_usuarios
FROM gold.dim_usuario
GROUP BY modos_identificados
ORDER BY cantidad_usuarios DESC;

/* Validar distribución de usuarios por cantidad de modos */
SELECT
    cantidad_modos,
    COUNT(*) AS cantidad_usuarios
FROM features.features_usuario_movilidad
GROUP BY cantidad_modos
ORDER BY cantidad_modos;;

/* Validar usuarios multimodales */
SELECT
    COUNT(*) AS usuarios_multimodales
FROM features.features_usuario_movilidad
WHERE es_multimodal = TRUE;

/* Ver columnas reales de dim_zona */
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'gold'
  AND table_name = 'dim_zona'
ORDER BY ordinal_position;

/* Ver columnas reales de dim_modo */
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'gold'
  AND table_name = 'dim_modo'
ORDER BY ordinal_position;

/* Ver columnas reales de fct_abordajes */
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'gold'
  AND table_name = 'fct_abordajes'
ORDER BY ordinal_position;

/* FASE 02 - CASO METRORIEL - Demanda en zonas 12, 8, 1, 6 y 17 */

SELECT
    zona_nombre,
    modo_nombre,
    SUM(cantidad_abordajes) AS total_abordajes
FROM gold.fct_abordajes
WHERE zona_nombre IN (
    'Zona 12',
    'Zona 8',
    'Zona 1',
    'Zona 6',
    'Zona 17'
)
GROUP BY
    zona_nombre,
    modo_nombre
ORDER BY
    zona_nombre,
    total_abordajes DESC;

/* COMPARACION DE DEMANDA EN ZONAS OBJETIVO
   Caso MetroRiel */

SELECT
    zona_nombre,
    SUM(cantidad_abordajes) AS demanda_total
FROM gold.fct_abordajes
WHERE zona_nombre IN (
    'Zona 12',
    'Zona 8',
    'Zona 1',
    'Zona 6',
    'Zona 17'
)
GROUP BY zona_nombre
ORDER BY demanda_total DESC;

/* REVISAR COLUMNAS DE LAS TABLAS SILVER PARA FEATURES */

SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'silver'
  AND table_name IN (
      'aerometro_boardings',
      'metroriel_viajes',
      'transmetro_validaciones',
      'transurbano_transacciones',
      'dim_usuario_conformado'
  )
ORDER BY table_name, ordinal_position;