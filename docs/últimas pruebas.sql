-- Evidencia: cantidad de usuarios con features de movilidad
SELECT COUNT(*) AS total_usuarios
FROM features.features_usuario_movilidad;

-- Evidencia: características de movilidad por usuario
SELECT *
FROM features.features_usuario_movilidad
LIMIT 10;

-- Distribución de usuarios por cantidad de modos identificados
SELECT
    cantidad_modos_identificados,
    COUNT(*) AS total_usuarios
FROM gold.dim_usuario
GROUP BY cantidad_modos_identificados
ORDER BY cantidad_modos_identificados;

-- Demanda total por modo de transporte
SELECT
    modo_nombre,
    SUM(abordajes) AS total_abordajes
FROM gold.rpt_demanda_red
GROUP BY modo_nombre
ORDER BY total_abordajes DESC;

-- Ranking de demanda existente sin contar MetroRiel
SELECT
    ranking_demanda_sin_metroriel,
    zona_nombre,
    demanda_sin_metroriel,
    en_trazado_metroriel
FROM gold.rpt_cobertura_zona
ORDER BY ranking_demanda_sin_metroriel;

-- Comparación de registros entre Silver y Gold
SELECT
    'Silver - Validaciones Transmetro' AS conjunto,
    COUNT(*) AS total_registros
FROM silver.transmetro_validaciones

UNION ALL

SELECT
    'Gold - Abordajes' AS conjunto,
    COUNT(*) AS total_registros
FROM gold.fct_abordajes;