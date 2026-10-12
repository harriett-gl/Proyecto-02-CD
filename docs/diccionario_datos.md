# Diccionario de datos

> Documento generado con `python scripts/generar_diccionario.py` desde los archivos `.yml` de dbt. No editar a mano: se edita el `.yml` y se vuelve a generar.

Para cada campo se indica qué significa, de qué fuente sale y qué transformación se le aplicó. El linaje gráfico está en [`docs/linaje/linaje_dbt.png`](linaje/linaje_dbt.png).

## Capa Gold - dimensiones

### `gold.dim_modo`

Catálogo de los cuatro modos de transporte.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `modo_sk` | Identificador numérico del modo de transporte. | Catálogo definido en dim_modo.sql | Asignación de claves numéricas a cada modo. |
| `modo_nombre` | Nombre estandarizado del operador. | Catálogo definido en dim_modo.sql | Asignación de claves numéricas a cada modo. |

### `gold.dim_hora`

Dimensión horaria con 24 horas y clasificación de franjas.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `hora_sk` | Clave de la hora en formato entero de 0 a 23. | Serie de horas generada en PostgreSQL | Generación de horas de 0 a 23 y clasificación horaria. |

### `gold.dim_fecha`

Calendario de fechas del período registrado en la red.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `fecha_sk` | Clave de fecha en formato YYYYMMDD. | Fechas de los cuatro operadores en Silver | Generación de calendario entre la fecha mínima y máxima. |
| `fecha` | Fecha calendario correspondiente a la clave. | Fechas de los cuatro operadores en Silver | Generación de calendario entre la fecha mínima y máxima. |

### `gold.dim_usuario`

Usuarios conformados y sus modos de transporte identificados.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `usuario_sk` | Identificador seudonimizado del usuario. | silver.dim_usuario_conformado | Agrupación por usuario y agregación de atributos y modos. |

### `gold.dim_zona`

Catálogo de zonas geográficas normalizadas.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `zona_sk` | Identificador de la zona. | silver.dim_zona_conformada | Proyección de las claves y nombres conformados. |
| `zona_nombre` | Nombre normalizado de la zona. | silver.dim_zona_conformada | Proyección de las claves y nombres conformados. |

## Capa Gold - tablas de hechos

### `gold.fct_abordajes`

Un abordaje válido de Transmetro, Transurbano o Aerometro por fila.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `abordaje_sk` | Clave única MD5 del modo y evento original. | Silver: transmetro_validaciones, transurbano_transacciones y aerometro_boardings | Unión de abordajes, normalización de zonas y enlace con dimensiones. |
| `modo_sk` | Clave del modo de transporte. | Silver: transmetro_validaciones, transurbano_transacciones y aerometro_boardings | Unión de abordajes, normalización de zonas y enlace con dimensiones. |
| `usuario_sk` | Clave seudonimizada del usuario. | Silver: transmetro_validaciones, transurbano_transacciones y aerometro_boardings | Unión de abordajes, normalización de zonas y enlace con dimensiones. |
| `fecha_sk` | Fecha del abordaje en formato YYYYMMDD. | Silver: transmetro_validaciones, transurbano_transacciones y aerometro_boardings | Unión de abordajes, normalización de zonas y enlace con dimensiones. |
| `hora_sk` | Hora local del abordaje. | Silver: transmetro_validaciones, transurbano_transacciones y aerometro_boardings | Unión de abordajes, normalización de zonas y enlace con dimensiones. |
| `cantidad_abordajes` | Indicador unitario de abordaje; valor 1. | Silver: transmetro_validaciones, transurbano_transacciones y aerometro_boardings | Unión de abordajes, normalización de zonas y enlace con dimensiones. |

### `gold.fct_viajes_metroriel`

Un viaje completo y válido de MetroRiel por fila.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `viaje_sk` | Clave MD5 generada a partir del identificador del viaje. | silver.metroriel_viajes | Enlace de viajes válidos con dimensiones y cálculo de claves. |
| `modo_sk` | Clave correspondiente a MetroRiel. | silver.metroriel_viajes | Enlace de viajes válidos con dimensiones y cálculo de claves. |
| `usuario_sk` | Clave seudonimizada del usuario. | silver.metroriel_viajes | Enlace de viajes válidos con dimensiones y cálculo de claves. |
| `fecha_sk` | Fecha de entrada en formato YYYYMMDD. | silver.metroriel_viajes | Enlace de viajes válidos con dimensiones y cálculo de claves. |
| `duracion_segundos` | Duración del viaje expresada en segundos. | silver.metroriel_viajes | Enlace de viajes válidos con dimensiones y cálculo de claves. |
| `cantidad_viajes` | Indicador unitario de viaje; valor 1. | silver.metroriel_viajes | Enlace de viajes válidos con dimensiones y cálculo de claves. |

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
