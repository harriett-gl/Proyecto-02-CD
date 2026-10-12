-- El tablero de cobertura debe incluir zonas de residencia sin servicio:
-- toda zona del padrón vigente debe aparecer en rpt_cobertura_zona.
select distinct {{ normalizar_zona('zona_residencia') }} as zona_faltante
from {{ ref('dim_usuario_actual') }}
where nullif(trim(zona_residencia), '') is not null
except
select zona_nombre from {{ ref('rpt_cobertura_zona') }}
