-- MEDICIÓN DEL TAMAÑO DE LAS CAPAS EN POSTGRESQL
-- PROYECTO RED METROPOLITANA - FASE 01
-- Incluye tablas normales y vistas materializadas.
-- Bronze se mide por separado desde el sistema de archivos.

WITH tamanos_postgresql AS (
    SELECT
        n.nspname AS capa,
        SUM(pg_total_relation_size(c.oid)) AS tamano_bytes
    FROM pg_class c
    JOIN pg_namespace n
        ON n.oid = c.relnamespace
    WHERE n.nspname IN (
        'staging',
        'silver',
        'gold',
        'quarantine',
        'audit'
    )
      AND c.relkind IN ('r', 'm')
    GROUP BY n.nspname
)

SELECT
    capa,
    pg_size_pretty(tamano_bytes) AS tamano_total,
    'PostgreSQL' AS fuente_medicion
FROM tamanos_postgresql

UNION ALL

SELECT
    'bronze' AS capa,
    '67 MB' AS tamano_total,
    'Sistema de archivos' AS fuente_medicion

ORDER BY capa;