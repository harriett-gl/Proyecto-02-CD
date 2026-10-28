# Diccionario de datos

> Documento generado con `python scripts/generar_diccionario.py` desde los archivos `.yml` de dbt. No editar a mano: se edita el `.yml` y se vuelve a generar.

Para cada campo se indica qué significa, de qué fuente sale y qué transformación se le aplicó. El linaje gráfico está en [`docs/linaje/linaje_dbt.png`](linaje/linaje_dbt.png).

## Capa Gold - dimensiones

### `gold.dim_modo`

Dimensión que contiene el catálogo estandarizado de los cuatro modos de transporte de la Red Metropolitana.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `modo_sk` | Identificador numérico único del modo de transporte. | Catálogo definido en dim_modo.sql | Asignación de una clave numérica a cada modo. |
| `modo_nombre` | Nombre estandarizado del modo de transporte. | Catálogo definido en dim_modo.sql | Estandarización de los nombres de los cuatro modos. |

### `gold.dim_hora`

Dimensión temporal que representa las 24 horas del día y permite analizar los registros de movilidad por hora y franja horaria.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `hora_sk` | Clave numérica que identifica cada hora del día, de 0 a 23. | Serie de horas generada en PostgreSQL | Generación de una secuencia de enteros de 0 a 23. |
| `hora` | Hora del día representada mediante un número entero. | Serie de horas generada en PostgreSQL | Generación de valores horarios entre 0 y 23. |
| `franja_horaria` | Categoría horaria utilizada para analizar los períodos del día. | gold.dim_hora | Clasificación de las horas en franjas horarias. |
| `es_hora_pico` | Indicador booleano que identifica los horarios de mayor demanda. | gold.dim_hora | Identificación de horas pico según las reglas del modelo. |

### `gold.dim_fecha`

Dimensión calendario que permite analizar la movilidad durante el período registrado en las fuentes de transporte.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `fecha_sk` | Identificador numérico de la fecha en formato YYYYMMDD. | Fechas de los cuatro operadores en Silver | Conversión de la fecha a una clave numérica YYYYMMDD. |
| `fecha` | Fecha calendario correspondiente al identificador. | Fechas de los cuatro operadores en Silver | Generación de fechas consecutivas dentro del período analizado. |
| `dia` | Día del mes correspondiente a la fecha. | gold.dim_fecha | Extracción del día de la fecha calendario. |
| `mes` | Número del mes correspondiente a la fecha. | gold.dim_fecha | Extracción del mes de la fecha calendario. |
| `anio` | Año correspondiente a la fecha. | gold.dim_fecha | Extracción del año de la fecha calendario. |
| `trimestre` | Trimestre del año al que pertenece la fecha. | gold.dim_fecha | Clasificación de la fecha en uno de los cuatro trimestres. |
| `dia_semana` | Número que representa el día de la semana. | gold.dim_fecha | Obtención del día de la semana a partir de la fecha. |
| `es_dia_habil` | Indicador booleano que identifica los días hábiles. | gold.dim_fecha | Clasificación de los días según el calendario laboral. |
| `es_fin_semana` | Indicador booleano que identifica los fines de semana. | gold.dim_fecha | Clasificación de los días correspondientes al fin de semana. |

### `gold.dim_usuario`

Dimensión de usuarios conformados de la Red Metropolitana. Integra los identificadores de los diferentes operadores y permite analizar la utilización de uno o varios modos de transporte.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `usuario_sk` | Identificador seudonimizado del usuario mediante HMAC-SHA256 con una clave secreta configurada en USUARIO_SALT. | silver.dim_usuario_conformado | Consolidación de la clave seudonimizada del usuario. |
| `perfil` | Perfil del usuario registrado en el padrón de Transmetro. | silver.dim_usuario_conformado | Consolidación del perfil disponible para el usuario. |
| `zona_residencia` | Zona de residencia asociada al usuario en el padrón. | silver.dim_usuario_conformado | Consolidación de la zona de residencia disponible. |
| `activo_en_transmetro` | Indicador del estado activo del usuario en Transmetro. | silver.dim_usuario_conformado | Consolidación del estado de actividad registrado en el padrón. |
| `modos_identificados` | Lista de modos de transporte asociados al usuario. | silver.dim_usuario_conformado | Agrupación de los nombres de los modos identificados. |
| `cantidad_modos_identificados` | Cantidad de modos de transporte distintos asociados al usuario. | silver.dim_usuario_conformado | Conteo de modos de transporte distintos por usuario. |

### `gold.dim_zona`

Dimensión geográfica que contiene las zonas normalizadas utilizadas para el análisis territorial de la movilidad.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `zona_sk` | Identificador único de la zona geográfica. | silver.dim_zona_conformada | Obtención del identificador de zona conformado. |
| `zona_nombre` | Nombre estandarizado de la zona geográfica. | silver.dim_zona_conformada | Obtención del nombre normalizado de la zona. |

## Capa Gold - tablas de hechos

### `gold.fct_abordajes`

Tabla de hechos que registra un abordaje válido de Transmetro, Transurbano o Aerómetro por fila. Permite analizar la demanda de transporte mediante dimensiones temporales, geográficas y de usuarios.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `abordaje_sk` | Identificador único del abordaje generado mediante MD5. | Identificadores de eventos de los tres operadores en Silver | Generación de una clave única a partir del modo y evento original. |
| `evento_origen_id` | Identificador del evento en el sistema de origen. | Eventos de los operadores en Silver | Conservación del identificador original del evento. |
| `modo_nombre` | Nombre del modo de transporte asociado al abordaje. | Catálogo de modos de transporte | Asociación del evento con su modo correspondiente. |
| `zona_sk` | Identificador de la zona asociada al abordaje. | Datos geográficos de los eventos en Silver | Asociación del evento con la zona normalizada. |
| `zona_nombre` | Nombre de la zona asociada al abordaje. | Datos geográficos de los eventos en Silver | Obtención del nombre normalizado de la zona. |
| `ubicacion_codigo` | Código de ubicación registrado para el evento. | Eventos de los operadores en Silver | Conservación del código de ubicación del evento. |
| `servicio` | Servicio de transporte asociado al abordaje. | Eventos de los operadores en Silver | Estandarización del servicio asociado al evento. |
| `fecha_hora_local` | Fecha y hora local del abordaje. | Fecha y hora del evento en Silver | Obtención de la marca temporal local del evento. |
| `monto_gtq` | Monto monetario del abordaje expresado en quetzales. | Datos monetarios de los operadores en Silver | Normalización del monto a quetzales. |
| `operacion_exitosa` | Indicador booleano del resultado de la operación. | Eventos de los operadores en Silver | Identificación del estado exitoso de la operación. |
| `modo_sk` | Clave que identifica el modo de transporte utilizado. | gold.dim_modo | Asociación del abordaje con el catálogo de modos. |
| `usuario_sk` | Identificador seudonimizado del usuario que realizó el abordaje. | silver.dim_usuario_conformado | Asociación del abordaje con la clave seudonimizada del usuario. |
| `fecha_sk` | Identificador de la fecha del abordaje en formato YYYYMMDD. | Fechas de los eventos registrados en Silver | Conversión de la fecha del evento a una clave de calendario. |
| `hora_sk` | Identificador de la hora en que ocurrió el abordaje. | Horas de los eventos registrados en Silver | Extracción de la hora del evento y asociación con la dimensión horaria. |
| `cantidad_abordajes` | Medida aditiva que representa un abordaje válido. Cada registro tiene un valor unitario de 1. | Eventos válidos de Transmetro, Transurbano y Aerómetro | Asignación del valor 1 a cada abordaje válido. |

### `gold.fct_viajes_metroriel`

Tabla de hechos que registra un viaje completo y válido de MetroRiel por fila. Permite analizar la cantidad de viajes y su duración.

| Campo | Significado | Fuente | Transformación |
|---|---|---|---|
| `viaje_sk` | Identificador único del viaje generado mediante MD5. | silver.metroriel_viajes | Generación de una clave a partir del identificador del viaje. |
| `viaje_id` | Identificador original del viaje de MetroRiel. | silver.metroriel_viajes | Conservación del identificador del viaje. |
| `modo_nombre` | Nombre del modo de transporte, correspondiente a MetroRiel. | Catálogo de modos de transporte | Asociación del viaje con el modo MetroRiel. |
| `zona_entrada_sk` | Identificador de la zona donde comienza el viaje. | silver.metroriel_viajes | Asociación de la zona de entrada con la dimensión geográfica. |
| `zona_salida_sk` | Identificador de la zona donde finaliza el viaje. | silver.metroriel_viajes | Asociación de la zona de salida con la dimensión geográfica. |
| `zona_entrada` | Nombre de la zona de origen del viaje. | silver.metroriel_viajes | Normalización del nombre de la zona de entrada. |
| `zona_salida` | Nombre de la zona de destino del viaje. | silver.metroriel_viajes | Normalización del nombre de la zona de salida. |
| `hora_entrada_sk` | Clave horaria correspondiente a la entrada del viaje. | silver.metroriel_viajes | Extracción de la hora de entrada del viaje. |
| `hora_salida_sk` | Clave horaria correspondiente a la salida del viaje. | silver.metroriel_viajes | Extracción de la hora de salida del viaje. |
| `estacion_entrada_id` | Identificador de la estación donde inicia el viaje. | silver.metroriel_viajes | Conservación del identificador de la estación de entrada. |
| `estacion_entrada` | Nombre de la estación donde inicia el viaje. | silver.metroriel_viajes | Obtención del nombre de la estación de entrada. |
| `estacion_salida_id` | Identificador de la estación donde finaliza el viaje. | silver.metroriel_viajes | Conservación del identificador de la estación de salida. |
| `estacion_salida` | Nombre de la estación donde finaliza el viaje. | silver.metroriel_viajes | Obtención del nombre de la estación de salida. |
| `fecha_hora_entrada` | Fecha y hora de inicio del viaje. | silver.metroriel_viajes | Obtención de la marca temporal de entrada. |
| `fecha_hora_salida` | Fecha y hora de finalización del viaje. | silver.metroriel_viajes | Obtención de la marca temporal de salida. |
| `monto_gtq` | Importe monetario del viaje expresado en quetzales. | silver.metroriel_viajes | Normalización del importe monetario a quetzales. |
| `modo_sk` | Clave del modo de transporte correspondiente a MetroRiel. | gold.dim_modo | Asociación del viaje con el modo MetroRiel. |
| `usuario_sk` | Identificador seudonimizado del usuario que realizó el viaje. | silver.dim_usuario_conformado | Asociación del viaje con la clave seudonimizada del usuario. |
| `fecha_sk` | Identificador de la fecha de entrada en formato YYYYMMDD. | silver.metroriel_viajes | Conversión de la fecha de entrada a una clave de calendario. |
| `duracion_segundos` | Duración del viaje expresada en segundos. Es una medida cuantitativa que permite calcular duraciones totales y promedios de viaje. | silver.metroriel_viajes | Obtención de la duración del viaje en segundos. |
| `cantidad_viajes` | Medida aditiva que representa un viaje válido de MetroRiel. Cada registro tiene un valor unitario de 1. | silver.metroriel_viajes | Asignación del valor 1 a cada viaje válido. |

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
