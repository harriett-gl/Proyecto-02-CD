# Evaluación del modelo de predicción de abandono

## 1. Objetivo

Predecir el riesgo de abandono de usuarios de la Red Metropolitana
de Transporte mediante características históricas de movilidad.

La unidad de análisis es el usuario conformado, identificado
mediante `usuario_sk`.

## 2. Cortes temporales

| Corte | Fecha | Usuarios | Uso |
|---|---|---:|---|
| A | 2026-07-01 | 59,796 | Entrenamiento y validación cruzada |
| B | 2026-07-31 | 58,372 | Evaluación temporal |
| C | 2026-08-30 | 57,925 | Predicción |

La población elegible incluye usuarios con al menos dos viajes
válidos durante los 28 días anteriores al corte.

Se define abandono como la ausencia de viajes válidos durante
los 30 días posteriores al corte.

El corte C conserva etiquetas nulas porque se utiliza para
generar predicciones, no para evaluar abandonos confirmados.

## 3. Características utilizadas

El modelo utiliza 14 características de movilidad:

- trips_28d
- trips_7d
- active_days_28d
- days_since_last_trip
- transport_modes_count
- is_multimodal
- transmetro_trips
- transurbano_trips
- metroriel_trips
- aerometro_trips
- weekend_trip_ratio
- peak_hour_trip_ratio
- total_spending_gtq
- average_spending_gtq

Todas las características se calculan con información anterior
a la fecha de corte.

## 4. Entrenamiento y selección

Se utilizó el corte A, con 59,796 usuarios y 7,396 casos
positivos de abandono.

Se aplicó validación cruzada estratificada de cinco particiones,
con semilla aleatoria 42.

Se compararon dos baselines y regresión logística con
regularización L1 y L2.

| Modelo | PR-AUC CV | ROC-AUC CV |
|---|---:|---:|
| Regresión logística L2 | 0.429148 | 0.835311 |
| Regresión logística L1 | 0.428200 | 0.833428 |
| Baseline frecuencia | 0.262542 | 0.744015 |
| Baseline constante | 0.123687 | 0.500000 |

Se seleccionó regresión logística L2 con C = 0.001,
por obtener la mayor PR-AUC promedio.

## 5. Evaluación temporal en B

El modelo entrenado con A se aplicó al corte B sin reentrenamiento.

Usuarios evaluados: 58,372.
Abandonos reales: 6,671.
Tasa de abandono: 11.43%.

| Modelo | PR-AUC | ROC-AUC |
|---|---:|---:|
| Regresión logística L2 | 0.387224 | 0.837086 |
| Baseline frecuencia | 0.253175 | 0.751937 |
| Baseline constante | 0.114284 | 0.500000 |

La regresión logística supera ambos baselines en el corte B.

La PR-AUC disminuye respecto de la validación cruzada en A,
mientras que la ROC-AUC permanece aproximadamente estable.

## 6. Clasificación con umbral 0.5

| Métrica | Valor |
|---|---:|
| Precisión | 0.524617 |
| Recall | 0.194873 |
| F1-score | 0.284184 |
| Verdaderos positivos | 1,300 |
| Falsos positivos | 1,178 |
| Falsos negativos | 5,371 |
| Verdaderos negativos | 50,523 |

El umbral 0.5 permite identificar un grupo de alto riesgo,
pero presenta sensibilidad limitada.

Para priorizar intervenciones puede ser más útil ordenar
a los usuarios por probabilidad estimada de abandono.

## 7. Predicciones del corte C

Se generaron probabilidades para 57,925 usuarios.

Probabilidad media estimada: 0.1536.

Usuarios con probabilidad igual o superior a 0.5: 2,293.

Estas predicciones no representan abandonos confirmados.

## 8. Control de fuga temporal

Las características se calculan exclusivamente con viajes
anteriores al corte correspondiente.

La auditoría independiente del corte A reportó:

- Usuarios originales: 59,796.
- Usuarios recalculados: 59,796.
- Usuarios con diferencias: 0.
- Resultado: PASS.

La validación cruzada se realizó únicamente en A.
El corte B se utilizó como evaluación temporal posterior.

## 9. Archivos de evidencia

- outputs/churn/model_comparison_A.csv
- outputs/churn/regularization_cv_A.csv
- outputs/churn/regularization_curve_A.png
- outputs/churn/logistic_coefficients_A.csv
- outputs/churn/training_log_A.txt
- outputs/churn/temporal_evaluation_B.csv
- outputs/churn/classification_metrics_B.csv
- outputs/churn/churn_predictions_C.csv

## 10. Limitaciones

La evaluación temporal muestra una reducción de PR-AUC
respecto de la validación cruzada.

El umbral 0.5 presenta recall limitado y no debe
considerarse automáticamente el umbral óptimo.

Las predicciones del corte C requieren observaciones futuras
para confirmar el abandono real.

Los resultados no demuestran causalidad entre las
características y el abandono.
