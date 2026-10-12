# Diccionario de datos

> Documento generado con `python scripts/generar_diccionario.py` desde los archivos `.yml` de dbt. No editar a mano: se edita el `.yml` y se vuelve a generar.


## Capa Gold - dimensiones

### `gold.dim_modo`



| Campo | Significado |
|---|---|
| `modo_sk` |  |
| `modo_nombre` |  |

### `gold.dim_hora`



| Campo | Significado |
|---|---|
| `hora_sk` |  |

### `gold.dim_fecha`



| Campo | Significado |
|---|---|
| `fecha_sk` |  |
| `fecha` |  |

### `gold.dim_usuario`



| Campo | Significado |
|---|---|
| `usuario_sk` |  |

### `gold.dim_zona`



| Campo | Significado |
|---|---|
| `zona_sk` |  |
| `zona_nombre` |  |

## Capa Gold - tablas de hechos

### `gold.fct_abordajes`

Un abordaje válido de Transmetro, Transurbano o Aerómetro por fila.

| Campo | Significado |
|---|---|
| `abordaje_sk` |  |
| `modo_sk` |  |
| `usuario_sk` |  |
| `fecha_sk` |  |
| `hora_sk` |  |
| `cantidad_abordajes` |  |

### `gold.fct_viajes_metroriel`

Un viaje completo y válido de MetroRiel por fila.

| Campo | Significado |
|---|---|
| `viaje_sk` |  |
| `modo_sk` |  |
| `usuario_sk` |  |
| `fecha_sk` |  |
| `duracion_segundos` |  |
| `cantidad_viajes` |  |

## Capa Gold - vistas para el tablero

### `gold.rpt_cobertura_zona`

Vista para el tablero (cobertura y caso MetroRiel). Una fila por zona del área metropolitana, incluyendo zonas donde vive gente según el padrón pero ningún modo opera.

**Dueño:** Dirección de Planificación Territorial

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `zona_sk` | md5 del nombre de zona (misma fórmula que dim_zona). | dim_zona + padrón | md5(zona_nombre) |
| `zona_nombre` | Nombre normalizado de la zona. | gold.dim_zona y silver.dim_usuario_actual.zona_residencia | UNION + macro normalizar_zona |
| `residentes_padron` | Tarjetas del padrón vigente con esa zona de residencia. | cdc_padron_usuarios.csv -> silver.dim_usuario_actual | count(*) por zona |
| `residentes_activos` | Tarjetas activas del padrón con esa zona de residencia. | silver.dim_usuario_actual | count(*) filter (activo) |
| `abordajes_transmetro` | Abordajes válidos de Transmetro en la zona. | gold.fct_abordajes | count por zona y modo |
| `abordajes_transurbano` | Abordajes válidos (aprobados) de Transurbano en la zona. | gold.fct_abordajes | count por zona y modo |
| `abordajes_aerometro` | Abordajes de Aerómetro en la zona. | gold.fct_abordajes | count por zona y modo |
| `viajes_metroriel_origen` | Viajes completos de MetroRiel que inician en la zona. | gold.fct_viajes_metroriel | count por zona_entrada |
| `viajes_metroriel_destino` | Viajes completos de MetroRiel que terminan en la zona. | gold.fct_viajes_metroriel | count por zona_salida |
| `modos_con_servicio` | Cantidad de modos (0-4) con actividad en la zona. | Columnas anteriores | Suma de banderas > 0 |
| `sin_servicio` | Verdadero si ningún modo registró actividad en la zona. | Columnas anteriores | total = 0 |
| `en_trazado_metroriel` | Verdadero para las zonas del trazado propuesto: 12, 8, 1, 6 y 17. | Enunciado del proyecto | Macro zonas_trazado_metroriel |
| `demanda_sin_metroriel` | Abordajes de Transmetro + Transurbano + Aerómetro: demanda que existe independientemente de MetroRiel. | gold.fct_abordajes | Suma |
| `demanda_total` | demanda_sin_metroriel + viajes de MetroRiel que inician en la zona. | fct_abordajes + fct_viajes_metroriel | Suma |
| `ranking_demanda_sin_metroriel` | Posición de la zona por demanda_sin_metroriel (1 = mayor). | Columna demanda_sin_metroriel | rank() descendente |

### `gold.rpt_demanda_red`

Vista para el tablero: demanda de los CUATRO modos por zona, fecha y hora. Un viaje de MetroRiel cuenta como un abordaje en su zona y hora de entrada.

**Dueño:** Gerencia de Operaciones

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `modo_sk` | Llave del modo. | fct_abordajes / fct_viajes_metroriel | UNION ALL |
| `modo_nombre` | Nombre del modo (los cuatro). | fct_abordajes / fct_viajes_metroriel | UNION ALL |
| `zona_sk` | Zona del abordaje o de la entrada a MetroRiel. | fct_abordajes.zona_sk / fct_viajes_metroriel.zona_entrada_sk | UNION ALL |
| `zona_nombre` | Nombre normalizado de la zona. | Igual que zona_sk | UNION ALL |
| `fecha_sk` | Fecha local (YYYYMMDD). | Hechos Gold | UNION ALL |
| `hora_sk` | Hora local (0-23); para MetroRiel, hora de entrada. | Hechos Gold | UNION ALL |
| `franja_horaria` | Franja de dim_hora. | gold.dim_hora | Join por hora_sk |
| `es_hora_pico` | Bandera oficial de hora pico. | gold.dim_hora | Join por hora_sk |
| `es_dia_habil` | Lunes a viernes. | gold.dim_fecha | Join por fecha_sk |
| `abordajes` | Abordajes (o entradas a MetroRiel) en el grupo. Aditiva. | cantidad_abordajes / cantidad_viajes | sum |
| `ingreso_gtq` | Tarifa total cobrada en quetzales. Aditiva. | monto_gtq | sum |

## Capa Features (ciencia de datos)

### `features.features_usuario_movilidad`

Tabla de features para ciencia de datos (sección 2.3). Una fila por usuario con al menos un viaje válido hasta la fecha de corte (variable dbt `fecha_corte`, por defecto 2026-07-15). Se calcula desde Silver (detalle atómico), nunca desde Gold. Permite entrenar, por ejemplo, un modelo que prediga qué usuarios dejarán de viajar en los próximos 30 días.

**Dueño:** Equipo de Ciencia de Datos

| Campo | Significado |
|---|---|
| `usuario_sk` | Seudónimo del usuario (misma llave que gold.dim_usuario). |
| `fecha_corte` | Fecha de corte del cálculo. Ningún evento posterior se usa. |
| `perfil_padron` | Perfil tarifario según el padrón (solo usuarios con tarjeta Transmetro). |
| `viajes_ultimos_7d` | Viajes válidos en los 7 días que terminan en la fecha de corte. |
| `viajes_ultimos_30d` | Viajes válidos en los últimos 30 días. |
| `viajes_ultimos_90d` | Viajes válidos en los últimos 90 días (el periodo de datos es de 45 días). |
| `viajes_total` | Viajes válidos de todo el historial hasta la fecha de corte. |
| `dias_activos` | Días distintos con al menos un viaje. |
| `dias_desde_ultimo_viaje` | Días entre el último viaje y la fecha de corte (recencia). |
| `dias_desde_primer_viaje` | Días entre el primer viaje observado y la fecha de corte (antigüedad). |
| `modo_mas_usado` | Modo con más viajes; empate se resuelve alfabéticamente. |
| `cantidad_modos` | Modos distintos con viajes observados (1-4). |
| `es_multimodal` | Verdadero si viajó en 2 o más modos. |
| `viajes_transmetro` | Viajes válidos en Transmetro. |
| `viajes_transurbano` | Viajes válidos (aprobados) en Transurbano. |
| `viajes_metroriel` | Viajes completos en MetroRiel. |
| `viajes_aerometro` | Abordajes en Aerómetro. |
| `proporcion_hora_pico` | Fracción de viajes en hora pico oficial (06-08 y 16-18 h), entre 0 y 1. |
| `proporcion_fin_semana` | Fracción de viajes en sábado o domingo, entre 0 y 1. |
| `zona_origen_mas_frecuente` | Zona donde más aborda (para MetroRiel, zona de entrada). |
| `zonas_distintas` | Cantidad de zonas distintas donde abordó. |
| `gasto_total_gtq` | Gasto acumulado en quetzales. |
| `gasto_promedio_viaje_gtq` | Gasto promedio por viaje en quetzales. |
| `transacciones_rechazadas` | Transacciones rechazadas en Transurbano (saldo insuficiente o tarjeta inválida). |
