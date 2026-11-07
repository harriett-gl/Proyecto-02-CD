# Model Card — Predicción de Abandono de Usuarios

**Proyecto:** Red Metropolitana — Proyecto 02, Fase 02
**Versión del modelo:** `churn-pipeline-v1`
**Algoritmo:** Random Forest Classifier
**Fecha de corte de entrenamiento:** 2026-07-01 (A)
**Estado:** Modelo entrenado, evaluado y versionado

## 1. Objetivo

El modelo busca identificar usuarios de la Red Metropolitana que presentan mayor probabilidad de abandonar el servicio. Su propósito es apoyar campañas de retención, priorizando a los usuarios cuyo contacto podría generar un beneficio económico.

## 2. Datos utilizados

Se utilizaron tres cortes temporales:

| Corte | Fecha | Usuarios | Uso |
|---|---|---:|---|
| A | 2026-07-01 | 59,796 | Entrenamiento y validación cruzada |
| B | 2026-07-31 | 58,372 | Evaluación temporal |
| C | 2026-08-30 | 57,925 | Predicción sin etiquetas |

Se consideró elegible a un usuario con al menos dos viajes durante los 28 días anteriores a su fecha de corte.

Para los cortes etiquetados, se definió abandono (`churn = 1`) cuando el usuario no realizó viajes durante los 30 días posteriores al corte.

## 3. Características del modelo

Se utilizaron 14 características relacionadas con la actividad y los hábitos de movilidad:

- Cantidad de viajes en los últimos 28 y 7 días.
- Días activos y días desde el último viaje.
- Cantidad de medios de transporte utilizados.
- Indicador de usuario multimodal.
- Viajes por Transmetro, Transurbano, Metroriel y Aerómetro.
- Proporción de viajes en fines de semana.
- Proporción de viajes en horas pico.
- Gasto total y gasto promedio.

Las características se calcularon utilizando viajes anteriores a cada fecha de corte.

## 4. Entrenamiento y selección

Se comparó la regresión logística L2 con Random Forest utilizando cinco particiones estratificadas sobre el corte A.

| Modelo | PR-AUC entrenamiento | PR-AUC validación |
|---|---:|---:|
| Regresión logística L2 | 0.428522 | 0.429148 |
| Random Forest | 0.500067 | 0.435169 |

Random Forest obtuvo una mejora de aproximadamente 0.006 puntos de PR-AUC en validación, aunque también presentó una diferencia mayor entre entrenamiento y validación.

Se conservó como candidato para evaluar su utilidad económica. La mejora predictiva es pequeña y no demuestra por sí sola que su mayor complejidad esté justificada.

## 5. Variables importantes

La importancia por permutación identificó principalmente:

1. Días desde el último viaje.
2. Viajes en los últimos siete días.
3. Días activos durante los últimos 28 días.
4. Gasto total.
5. Proporción de viajes en horas pico.

Estas variables ayudan a identificar cambios en la frecuencia y los hábitos de movilidad.

## 6. Política de contacto

Se consideraron los siguientes valores:

- Costo por contacto: Q5.
- Probabilidad de éxito de una intervención: 25%.
- Valor estimado de retener un usuario: Q60.

El umbral económico teórico se calculó como:

**Q5 / (0.25 × Q60) = 0.333333**

La política seleccionada consiste en contactar a los usuarios con un puntaje superior al umbral.

En las predicciones fuera de muestra del corte A, la ganancia estimada fue de **Q12,715**.

## 7. Evaluación temporal en B

Se evaluó el modelo en el corte B utilizando la política establecida con el corte A.

| Métrica | Resultado |
|---|---:|
| PR-AUC | 0.399490 |
| Precisión | 0.432428 |
| Recall | 0.405786 |
| Verdaderos positivos | 2,707 |
| Falsos positivos | 3,553 |
| Falsos negativos | 3,964 |
| Verdaderos negativos | 48,148 |
| Usuarios a contactar | 6,260 |
| Ganancia estimada | Q9,305 |

El resultado muestra una ganancia económica positiva bajo los supuestos definidos.

El corte B ya había sido utilizado en una evaluación anterior de la regresión logística durante la Fase 01. Por ello, debe considerarse una evaluación temporal con exposición previa al conjunto B, y no una prueba completamente ciega.

## 8. Segmentación de usuarios

Se aplicó KMeans a las características estandarizadas del corte A.

Se seleccionaron dos segmentos:

| Segmento | Usuarios | Tasa de abandono |
|---|---:|---:|
| 0 | 48,956 | 14.69% |
| 1 | 10,840 | 1.90% |

El segmento 0 agrupa usuarios de menor actividad relativa y mayor riesgo de abandono. Se recomienda priorizar acciones de reactivación.

El segmento 1 presenta mayor frecuencia de uso y menor abandono. Se recomienda aplicar estrategias de fidelización.

La representación PCA de dos componentes explicó aproximadamente el 47.54% de la variabilidad.

## 9. Predicciones del corte C

El pipeline versionado se utilizó para generar predicciones del corte C sin reentrenamiento.

**Resultados:**

- Usuarios procesados: 57,925.
- Usuarios con tarjeta respaldada por CDC: 27,200.
- Usuarios sin tarjeta asociada en el CSV: 30,725.
- Usuarios seleccionados para contacto: 6,385.

El archivo generado contiene las columnas:

`unidad_id, tarjetas, puntaje, contactar`

El corte C no dispone de etiquetas de abandono, por lo que no se reportan métricas de desempeño predictivo para ese corte.


### Auditoría de cobertura de tarjetas del corte C

Se realizó una auditoría adicional sobre las 57,925 unidades
de análisis del corte C para determinar la causa de las tarjetas
vacías en el archivo de predicciones.

| Categoría | Usuarios | Porcentaje |
|---|---:|---:|
| Sin identidad Transmetro/Transurbano | 12,588 | 21.73% |
| Identidad TM/TU sin coincidencia CDC | 18,137 | 31.31% |
| Coincidencia CDC únicamente posterior al corte | 0 | 0.00% |
| Tarjeta válida al corte | 27,200 | 46.96% |
| **Total** | **57,925** | **100.00%** |

Las 30,725 unidades sin tarjeta recuperable representan el
53.04% de la población.

No se identificaron coincidencias CDC exclusivamente posteriores
al corte. Por lo tanto, se conservó el filtro temporal y no se
generaron identificadores artificiales.

La ausencia de tarjeta no impide calcular el puntaje de abandono,
pero limita la posibilidad de ejecutar campañas de contacto
basadas exclusivamente en tarjetas.

La auditoría se documenta en:

`docs/churn/card_identity_audit_C.md`

**Advertencia operativa:** los 6,385 usuarios seleccionados por
la política económica no deben interpretarse automáticamente
como 6,385 contactos ejecutables. La cantidad efectivamente
contactable debe calcularse considerando la disponibilidad de
identificadores y los canales autorizados.

## 10. Reproducibilidad

El modelo se encuentra guardado en:

`outputs/churn/models/churn_pipeline_v1.joblib`

El pipeline contiene el preprocesamiento de valores faltantes y el clasificador Random Forest previamente entrenado.

El archivo `requirements-phase2-lock.txt` registra las dependencias utilizadas.

Se verificó que el pipeline reproduce las 57,925 probabilidades del modelo original con una diferencia máxima de `2.22 × 10⁻¹⁶` y cero diferencias superiores a la tolerancia de `1e-12`.

Las auditorías de recálculo de características de los cortes A, B y C finalizaron sin diferencias.

## 11. Limitaciones

- Random Forest presenta una diferencia entre el rendimiento de entrenamiento y validación, lo que indica cierto sobreajuste.
- La mejora frente a regresión logística es limitada.
- La ganancia económica depende de supuestos de costo, efectividad y valor de retención; no representa ingresos reales observados.
- El corte B había sido examinado previamente en la Fase 01.
- Las auditorías de características reutilizan la población materializada, por lo que no prueban por completo la invariancia de la construcción de identidades.
- Las asociaciones de tarjetas tienen respaldo en registros CDC anteriores al corte C, pero no se reconstruyó históricamente toda la dimensión de identidad.
- No todos los usuarios cuentan con una tarjeta recuperable.
- Los puntajes no deben interpretarse automáticamente como probabilidades perfectamente calibradas.
- Los identificadores de usuarios y tarjetas deben protegerse y no publicarse innecesariamente.

## 12. Uso previsto

El modelo está destinado a apoyar decisiones de retención de usuarios de la Red Metropolitana.

No debe utilizarse como único criterio para restringir servicios, penalizar usuarios o tomar decisiones individuales perjudiciales.

Se recomienda monitorear periódicamente el desempeño, revisar la efectividad real de las campañas y actualizar el modelo cuando existan nuevos datos etiquetados.

## Aviso de datos simulados

Los datos de movilidad, usuarios, transacciones y tarjetas
utilizados en este proyecto son datos simulados con fines
exclusivamente académicos para el curso de Ciencia de Datos
de la Universidad Rafael Landívar, 2026, de conformidad con
el enunciado oficial del Proyecto 02.

No corresponden a datos personales ni bancarios reales.

El archivo `predictions_C_phase2.csv` contiene las columnas
`unidad_id`, `tarjetas`, `puntaje` y `contactar`, conforme
al formato solicitado para la entrega de la Fase 02.

Los identificadores de tarjetas pertenecen al conjunto de
datos sintéticos utilizado en el proyecto.
