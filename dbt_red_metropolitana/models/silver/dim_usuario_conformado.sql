with llaves_usuarios as (

    select
        usuario_natural_id as usuario_origen_id,
        'TRANSMETRO' as modo

    from {{ ref('dim_usuario_actual') }}

    union

    select
        usuario_origen_id,
        'TRANSMETRO' as modo

    from {{ ref('transmetro_validaciones') }}

    union

    select
        usuario_origen_id,
        'TRANSURBANO' as modo

    from {{ ref('cat_usuario_transurbano') }}

    union

    select
        usuario_origen_id,
        'METRORIEL' as modo

    from {{ ref('cat_usuario_metroriel') }}

    union

    select
        usuario_origen_id,
        'AEROMETRO' as modo

    from {{ ref('cat_usuario_aerometro') }}

),

usuarios_con_padron as (

    select
        llave.usuario_origen_id,
        llave.modo,

        case
            when llave.modo = 'TRANSMETRO'
                then padron.perfil
        end as perfil,

        case
            when llave.modo = 'TRANSMETRO'
                then padron.zona_residencia
        end as zona_residencia,

        case
            when llave.modo = 'TRANSMETRO'
                then padron.activo
        end as activo,

        case
            when llave.modo = 'TRANSMETRO'
                then padron.usuario_natural_id is not null
        end as registrado_en_padron

    from llaves_usuarios llave

    left join {{ ref('dim_usuario_actual') }} padron
        on llave.modo = 'TRANSMETRO'
       and llave.usuario_origen_id =
           padron.usuario_natural_id

)

select
   -- Seudonimización: md5 con una "sal" secreta (variable de entorno
   -- USUARIO_SALT, nunca en el repositorio). Sin la sal, el md5 de un
   -- número de 10 dígitos se podría revertir probando todos los valores.
   md5(
    '{{ env_var("USUARIO_SALT", "") }}' ||
    case
        when modo = 'TRANSMETRO'
             and usuario_origen_id ~ '^TC-[0-9]{8}$'
            then lpad(
                regexp_replace(usuario_origen_id, '[^0-9]', '', 'g'),
                10,
                '0'
            )

        when modo = 'TRANSURBANO'
             and usuario_origen_id ~ '^[0-9]{10}$'
            then usuario_origen_id

        when modo = 'METRORIEL'
             and usuario_origen_id ~ '^MR[0-9]{7}$'
            then lpad(
                regexp_replace(usuario_origen_id, '[^0-9]', '', 'g'),
                10,
                '0'
            )

        else modo || '|' || usuario_origen_id
    end
) as usuario_sk,

    usuario_origen_id,
    modo,
    perfil,
    zona_residencia,
    activo,
    registrado_en_padron

from usuarios_con_padron

where nullif(trim(usuario_origen_id), '') is not null