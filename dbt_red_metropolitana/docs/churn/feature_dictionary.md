# Diccionario de características — Predicción de abandono

## Configuración temporal

- Unidad de análisis: identificador de usuario conformado (`usuario_sk`).
- Corte A: 2026-07-01.
- Corte B: 2026-07-31.
- Corte C: 2026-08-30.
- Ventana de características: 28 días anteriores a cada corte.
- Zona horaria: America/Guatemala.
- Fuente de características: `churn.churn_features`.
- Fuentes de viajes: modelos Silver `transmetro_validaciones`, `transurbano_transacciones`, `metroriel_viajes` y `aerometro_boardings`, unificados mediante `churn_valid_trips`.
- No se utilizan viajes posteriores a la fecha de corte para calcular características.

## Características

| Variable | Descripción | Ventana | Fuente Silver |
|---|---|---|---|
| trips_28d | Cantidad de viajes válidos realizados por el usuario | 28 días  Cuatro fuentes Silver |
| trips_7d | Cantidad de viajes válidos recientes | 7 días  Cuatro fuentes Silver |
| active_days_28d | Número de días distintos con actividad | 28 días  Cuatro fuentes Silver |
| days_since_last_trip | Días transcurridos desde el último viaje | Hasta el corte  Cuatro fuentes Silver |
| transport_modes_count | Cantidad de modos de transporte utilizados | 28 días  Cuatro fuentes Silver |
| is_multimodal | Indicador de uso de más de un modo de transporte | 28 días  Cuatro fuentes Silver |
| transmetro_trips | Viajes realizados en Transmetro | 28 días  transmetro_validaciones |
| transurbano_trips | Viajes realizados en Transurbano | 28 días  transurbano_transacciones |
| metroriel_trips | Viajes realizados en Metroriel | 28 días  metroriel_viajes |
| aerometro_trips | Viajes realizados en Aerómetro | 28 días  aerometro_boardings |
| weekend_trip_ratio | Proporción de viajes realizados durante fines de semana | 28 días  Cuatro fuentes Silver |
| peak_hour_trip_ratio | Proporción de viajes realizados en horario pico | 28 días  Cuatro fuentes Silver |
| total_spending_gtq | Gasto total registrado en quetzales | 28 días  Cuatro fuentes Silver |
| average_spending_gtq | Gasto promedio por viaje registrado en quetzales | 28 días  Cuatro fuentes Silver |

## Control de fuga temporal

Se ejecutó una auditoría independiente para el corte A, comparando
las características calculadas con las tablas completas frente a
las características calculadas con viajes recortados antes del
1 de julio de 2026.

Resultados:

- Usuarios originales: 59,796.
- Usuarios recalculados: 59,796.
- Usuarios con diferencias: 0.
- Resultado: PASS.

## Validación de modelos

Se utilizaron cinco particiones estratificadas sobre el corte A,
con semilla aleatoria 42.

La métrica principal fue Average Precision (PR-AUC),
por ser apropiada para evaluar la priorización de la clase
minoritaria de abandono.

Resultados:

| Modelo | PR-AUC promedio | Desviación estándar |
|---|---:|---:|
| Baseline constante | 0.123687 | 0.000029 |
| Baseline frecuencia | 0.262542 | 0.004275 |
| Regresión logística L1 | 0.428200 | 0.014151 |
| Regresión logística L2 | 0.429148 | 0.014108 |

Modelo seleccionado: regresión logística L2.
Parámetro C: 0.001.

El corte B se mantiene reservado para la evaluación temporal
posterior y no se utilizó para seleccionar el modelo.
