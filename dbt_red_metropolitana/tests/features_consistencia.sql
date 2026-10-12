-- Coherencia interna de la tabla de features. Devuelve filas inválidas.
select *
from {{ ref('features_usuario_movilidad') }}
where viajes_ultimos_7d > viajes_ultimos_30d
   or viajes_ultimos_30d > viajes_ultimos_90d
   or viajes_ultimos_90d > viajes_total
   or viajes_total < 1
   or viajes_total <> viajes_transmetro + viajes_transurbano
                     + viajes_metroriel + viajes_aerometro
   or dias_activos > viajes_total
   or dias_desde_ultimo_viaje < 0
   or dias_desde_ultimo_viaje > dias_desde_primer_viaje
   or proporcion_hora_pico not between 0 and 1
   or proporcion_fin_semana not between 0 and 1
   or cantidad_modos not between 1 and 4
   or es_multimodal <> (cantidad_modos >= 2)
   or gasto_total_gtq < 0
