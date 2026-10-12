# Capa de features para ciencia de datos (sección 2.3)

| Elemento | Valor |
|---|---|
| Tabla | `features.features_usuario_movilidad` |
| Modelo dbt | `../../dbt_red_metropolitana/models/features/features_usuario_movilidad.sql` |
| Grano | Una fila por usuario (`usuario_sk`) con al menos un viaje válido |
| Fuente | **Solo Silver**: `transmetro_validaciones`, `transurbano_transacciones`, `metroriel_viajes`, `aerometro_boardings` y `dim_usuario_conformado` |
| **Fecha de corte declarada** | **2026-07-15** (último día con datos). Variable `fecha_corte` en `dbt_project.yml` |
| Filas | 70,380 usuarios |
| Pruebas | `unique`/`not_null`, `features_consistencia`, `features_sin_fuga_de_informacion`, `features_no_lee_gold` |

## Por qué sale de Silver y no de Gold

Gold ya agregó al grano de negocio (abordaje, viaje) y dejó fuera lo que el
tablero no necesita, por ejemplo las transacciones rechazadas de Transurbano.
La tabla de features parte del evento atómico de Silver y lo agrega a su manera
(ventanas de 7/30/90 días, recencia, proporciones). La prueba
`tests/features_no_lee_gold.sql` falla si alguien hace que el modelo dependa de Gold.

## Fecha de corte y fuga de información

Solo se usan eventos con fecha **menor o igual** a la fecha de corte. Para
entrenar un modelo se calcula la tabla con un corte anterior (por ejemplo
`dbt build --select features_usuario_movilidad --vars '{fecha_corte: "2026-06-30"}'`)
y la etiqueta se mide en los días posteriores.

## Qué se podría predecir

**Con esta tabla se puede entrenar un modelo que prediga qué usuarios dejarán de
viajar en los próximos 30 días (abandono), para que la Agencia detecte a tiempo
corredores o perfiles que pierden pasajeros y actúe antes de que se pasen al
vehículo particular.** También sirve para segmentar usuarios (pendulares de hora
pico, multimodales, ocasionales de fin de semana) y dimensionar tarifas integradas.

## Diccionario de la tabla

| Columna | Tipo | Significado |
|---|---|---|
| `usuario_sk` | texto | Seudónimo del usuario (misma llave que `gold.dim_usuario`) |
| `fecha_corte` | fecha | Fecha de corte del cálculo |
| `perfil_padron` | texto | Perfil tarifario según el padrón (solo usuarios con tarjeta Transmetro; nulo en otros) |
| `viajes_ultimos_7d` | entero | Viajes válidos en los 7 días que terminan en la fecha de corte |
| `viajes_ultimos_30d` | entero | Viajes válidos en los últimos 30 días |
| `viajes_ultimos_90d` | entero | Viajes válidos en los últimos 90 días (el periodo de datos es de 45) |
| `viajes_total` | entero | Viajes válidos de todo el historial hasta el corte |
| `dias_activos` | entero | Días distintos con al menos un viaje |
| `dias_desde_ultimo_viaje` | entero | Recencia: días entre el último viaje y el corte |
| `dias_desde_primer_viaje` | entero | Antigüedad observada |
| `modo_mas_usado` | texto | Modo con más viajes (empate: orden alfabético) |
| `cantidad_modos` | entero | Modos distintos con viajes (1-4) |
| `es_multimodal` | booleano | Verdadero si `cantidad_modos >= 2` |
| `viajes_transmetro` … `viajes_aerometro` | entero | Viajes por modo |
| `proporcion_hora_pico` | decimal 0-1 | Fracción de viajes en hora pico oficial (06-08 y 16-18 h) |
| `proporcion_fin_semana` | decimal 0-1 | Fracción de viajes en sábado o domingo |
| `zona_origen_mas_frecuente` | texto | Zona donde más aborda (MetroRiel: zona de entrada) |
| `zonas_distintas` | entero | Zonas distintas donde abordó |
| `gasto_total_gtq` | decimal | Gasto acumulado en quetzales |
| `gasto_promedio_viaje_gtq` | decimal | Gasto promedio por viaje |
| `transacciones_rechazadas` | entero | Rechazos de Transurbano (saldo insuficiente / tarjeta inválida); solo visible en Silver |

Un viaje válido sigue la definición oficial de [gobernanza.md](gobernanza.md).
