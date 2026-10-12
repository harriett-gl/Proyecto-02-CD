-- 1. CONTEOS EXACTOS POR TABLA Y CAPA
CREATE OR REPLACE FUNCTION pg_temp.conteos_fase1()
RETURNS TABLE (
    esquema TEXT,
    tabla TEXT,
    cantidad BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    registro RECORD;
BEGIN
    FOR registro IN
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
          AND table_schema IN (
              'staging',
              'silver',
              'gold',
              'quarantine'
          )
        ORDER BY table_schema, table_name
    LOOP
        RETURN QUERY EXECUTE format(
            'SELECT %L::text, %L::text, count(*)::bigint FROM %I.%I',
            registro.table_schema,
            registro.table_name,
            registro.table_schema,
            registro.table_name
        );
    END LOOP;
END;
$$;

SELECT *
FROM pg_temp.conteos_fase1()
ORDER BY esquema, tabla;

-- 2. OPERACIONES CDC
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'staging'
  AND table_name = 'cdc_padron_usuarios'
ORDER BY ordinal_position;

SELECT
    op AS operacion,
    count(*) AS cantidad
FROM staging.cdc_padron_usuarios
GROUP BY op
ORDER BY op;

-- 3. ESTADO ACTUAL DEL PADRÓN
SELECT
    activo,
    count(*) AS cantidad
FROM silver.dim_usuario_actual
GROUP BY activo
ORDER BY activo DESC;

-- 4. CATÁLOGOS MÍNIMOS DE USUARIOS
SELECT
    'Aerometro' AS operador,
    count(*) AS usuarios_distintos
FROM silver.cat_usuario_aerometro

UNION ALL

SELECT
    'MetroRiel',
    count(*)
FROM silver.cat_usuario_metroriel

UNION ALL

SELECT
    'Transurbano',
    count(*)
FROM silver.cat_usuario_transurbano

ORDER BY operador;

-- 5. RECHAZOS POR REGLA DE CALIDAD
CREATE OR REPLACE FUNCTION pg_temp.metricas_calidad()
RETURNS TABLE (
    tabla TEXT,
    motivo TEXT,
    cantidad BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    registro RECORD;
BEGIN
    FOR registro IN
        SELECT DISTINCT table_name
        FROM information_schema.columns
        WHERE table_schema = 'quarantine'
          AND column_name = 'motivo_rechazo'
        ORDER BY table_name
    LOOP
        RETURN QUERY EXECUTE format(
            'SELECT %L::text,
                    motivo_rechazo::text,
                    count(*)::bigint
             FROM quarantine.%I
             GROUP BY motivo_rechazo',
            registro.table_name,
            registro.table_name
        );
    END LOOP;
END;
$$;

SELECT *
FROM pg_temp.metricas_calidad()
ORDER BY tabla, motivo;

-- 6. ÚLTIMAS DOS EJECUCIONES
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