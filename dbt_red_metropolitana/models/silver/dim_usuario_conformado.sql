{% set usuario_salt = env_var('USUARIO_SALT') %}

{% if not usuario_salt | trim %}
    {{ exceptions.raise_compiler_error(
        "USUARIO_SALT no puede estar vacio"
    ) }}
{% endif %}

WITH llaves_usuarios AS (

    SELECT
        usuario_natural_id AS usuario_origen_id,
        'TRANSMETRO' AS modo
    FROM {{ ref('dim_usuario_actual') }}

    UNION

    SELECT
        usuario_origen_id,
        'TRANSMETRO' AS modo
    FROM {{ ref('transmetro_validaciones') }}

    UNION

    SELECT
        usuario_origen_id,
        'TRANSURBANO' AS modo
    FROM {{ ref('cat_usuario_transurbano') }}

    UNION

    SELECT
        usuario_origen_id,
        'METRORIEL' AS modo
    FROM {{ ref('cat_usuario_metroriel') }}

    UNION

    SELECT
        usuario_origen_id,
        'AEROMETRO' AS modo
    FROM {{ ref('cat_usuario_aerometro') }}

),

usuarios_con_padron AS (

    SELECT
        llave.usuario_origen_id,
        llave.modo,

        CASE
            WHEN llave.modo = 'TRANSMETRO'
                THEN padron.perfil
        END AS perfil,

        CASE
            WHEN llave.modo = 'TRANSMETRO'
                THEN padron.zona_residencia
        END AS zona_residencia,

        CASE
            WHEN llave.modo = 'TRANSMETRO'
                THEN padron.activo
        END AS activo,

        CASE
            WHEN llave.modo = 'TRANSMETRO'
                THEN padron.usuario_natural_id IS NOT NULL
        END AS registrado_en_padron

    FROM llaves_usuarios llave

    LEFT JOIN {{ ref('dim_usuario_actual') }} padron
        ON llave.modo = 'TRANSMETRO'
       AND llave.usuario_origen_id = padron.usuario_natural_id

),

normalizados AS (

    SELECT
        usuario_origen_id,
        modo,
        perfil,
        zona_residencia,
        activo,
        registrado_en_padron,

        CASE
            WHEN modo = 'TRANSMETRO'
                 AND usuario_origen_id ~ '^TC-[0-9]{8}$'
                THEN LPAD(
                    REGEXP_REPLACE(usuario_origen_id, '[^0-9]', '', 'g'),
                    10,
                    '0'
                )

            WHEN modo = 'TRANSURBANO'
                 AND usuario_origen_id ~ '^[0-9]{10}$'
                THEN usuario_origen_id

            WHEN modo = 'METRORIEL'
                 AND usuario_origen_id ~ '^MR[0-9]{7}$'
                THEN LPAD(
                    REGEXP_REPLACE(usuario_origen_id, '[^0-9]', '', 'g'),
                    10,
                    '0'
                )

            ELSE modo || '|' || usuario_origen_id

        END AS llave_normalizada

    FROM usuarios_con_padron

    WHERE NULLIF(TRIM(usuario_origen_id), '') IS NOT NULL

)

-- Generar identificadores seudonimizados mediante HMAC-SHA256
-- La clave USUARIO_SALT es obligatoria y debe mantenerse fuera de Git
SELECT
    ENCODE(
        HMAC(
            CONVERT_TO(llave_normalizada, 'UTF8'),
            CONVERT_TO('{{ env_var("USUARIO_SALT") }}', 'UTF8'),
            'sha256'
        ),
        'hex'
    ) AS usuario_sk,

    usuario_origen_id,
    modo,
    perfil,
    zona_residencia,
    activo,
    registrado_en_padron

FROM normalizados