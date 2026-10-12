-- La fecha de corte debe respetarse: ningún usuario puede tener su último
-- viaje después del corte y la fecha declarada debe ser la misma en todas las filas.
select fecha_corte, count(*) as filas
from {{ ref('features_usuario_movilidad') }}
group by fecha_corte
having fecha_corte <> date '{{ var("fecha_corte", "2026-07-15") }}'
    or min(dias_desde_ultimo_viaje) < 0
