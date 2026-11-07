# Proyecto 02 — Fase 02
## Informe técnico de predicción de abandono

### 1. Introducción

En esta segunda fase del proyecto Red Metropolitana se amplió el modelo de predicción de abandono desarrollado anteriormente. El objetivo fue comparar un modelo más complejo, establecer una política de contacto económicamente justificable, identificar grupos de usuarios y preparar un pipeline que pudiera generar predicciones sin necesidad de volver a entrenarse.

Se trabajó con información de movilidad de Transmetro, Transurbano, Metroriel y Aerómetro.

### 2. Datos utilizados

Se utilizaron tres cortes temporales:

| Corte | Fecha | Usuarios | Propósito |
|---|---|---:|---|
| A | 01/07/2026 | 59,796 | Entrenamiento y validación |
| B | 31/07/2026 | 58,372 | Evaluación temporal |
| C | 30/08/2026 | 57,925 | Predicción final |

Se utilizaron 14 características relacionadas con frecuencia de viajes, actividad reciente, uso de diferentes medios de transporte y gastos.

La etiqueta de abandono se definió como la ausencia de viajes durante los 30 días posteriores a cada corte etiquetado.

### 3. Apartado 2.1 — Modelo Ensemble

Se entrenó un modelo Random Forest y se comparó con la regresión logística L2 desarrollada en la Fase 01.

La evaluación utilizó cinco particiones estratificadas del corte A.

| Modelo | PR-AUC entrenamiento | PR-AUC validación |
|---|---:|---:|
| Regresión logística L2 | 0.428522 | 0.429148 |
| Random Forest | 0.500067 | 0.435169 |

Random Forest obtuvo una mejora de 0.006021 puntos de PR-AUC en validación.

Sin embargo, la diferencia entre entrenamiento y validación fue de aproximadamente 0.064898, indicando un mayor riesgo de sobreajuste.

**Conclusión:** Random Forest ofrece una mejora predictiva pequeña. Se utilizó para evaluar la política económica, aunque su mayor complejidad no queda plenamente justificada únicamente por la mejora de PR-AUC.

#### Importancia de variables

La importancia por permutación identificó como variables principales:

1. `days_since_last_trip`
2. `trips_7d`
3. `active_days_28d`
4. `total_spending_gtq`
5. `peak_hour_trip_ratio`

La actividad reciente fue especialmente importante para identificar riesgo de abandono.

**Evidencias:**
- `outputs/churn/model_comparison_phase2.csv`
- `outputs/churn/permutation_importance_A.csv`
- `outputs/churn/permutation_importance.png`

### 4. Apartado 2.2 — Política económica de contacto

Se utilizaron los siguientes supuestos:

| Concepto | Valor |
|---|---:|
| Costo por contacto | Q5 |
| Probabilidad de éxito | 25% |
| Valor de retención | Q60 |

El umbral económico teórico es:

**Umbral = 5 / (0.25 × 60) = 0.333333**

Se calculó la ganancia esperada utilizando predicciones fuera de muestra del corte A.

Con el umbral seleccionado se obtuvieron:

- Usuarios a contactar: 6,610.
- Verdaderos positivos: 3,051.
- Falsos positivos: 3,559.
- Ganancia esperada: Q12,715.

Aunque el máximo observado en A se obtuvo cerca de 0.355, se mantuvo el umbral teórico de 0.333333 para evitar ajustar la política exclusivamente a ese resultado.

#### Evaluación temporal en B

El modelo se aplicó al corte B sin reentrenamiento.

| Métrica | Resultado |
|---|---:|
| PR-AUC | 0.399490 |
| Precisión | 0.432428 |
| Recall | 0.405786 |
| Verdaderos positivos | 2,707 |
| Falsos positivos | 3,553 |
| Falsos negativos | 3,964 |
| Verdaderos negativos | 48,148 |
| Usuarios contactados | 6,260 |
| Ganancia esperada | Q9,305 |

La ganancia estimada fue positiva bajo los supuestos establecidos.

El corte B había sido evaluado previamente con regresión logística durante la Fase 01. Por ello, no debe describirse como un conjunto completamente desconocido para el proyecto.

**Evidencias:**
- `outputs/churn/gain_threshold.png`
- `outputs/churn/threshold_gain_A.csv`
- `outputs/churn/selected_policy_A.csv`
- `outputs/churn/ensemble_evaluation_B.csv`

### 5. Apartado 2.3 — Segmentación de usuarios

Se utilizó KMeans sobre las características estandarizadas del corte A.

Se analizaron diferentes valores de K mediante el método del codo y el coeficiente de silueta.

Se seleccionaron dos segmentos.

| Segmento | Usuarios | Porcentaje | Tasa de abandono |
|---|---:|---:|---:|
| 0 | 48,956 | 81.87% | 14.69% |
| 1 | 10,840 | 18.13% | 1.90% |

#### Interpretación

**Segmento 0:** usuarios con actividad moderada o baja y mayor riesgo de abandono. Su mediana fue de siete viajes en 28 días y cuatro días desde el último viaje.

Se recomiendan campañas de reactivación y recordatorios de beneficios del servicio.

**Segmento 1:** usuarios frecuentes y con menor riesgo de abandono. Su mediana fue de 37 viajes en 28 días y un día desde el último viaje.

Se recomiendan estrategias de fidelización y beneficios por uso frecuente.

#### Análisis PCA

Se utilizaron dos componentes principales:

- Primera componente: 31.78% de varianza explicada.
- Segunda componente: 15.76%.
- Varianza acumulada: 47.54%.

La proyección PCA permitió visualizar la distribución aproximada de los segmentos, aunque no representa toda la variabilidad de los datos.

**Evidencias:**
- `outputs/churn/kmeans_elbow.png`
- `outputs/churn/kmeans_silhouette.png`
- `outputs/churn/pca_segments.png`
- `outputs/churn/kmeans_segments_A.csv`

### 6. Apartado 2.4 — Pipeline reproducible

Se guardó un pipeline versionado que incluye el preprocesamiento y el clasificador Random Forest entrenado.

**Modelo:**

`outputs/churn/models/churn_pipeline_v1.joblib`

**Script de predicción:**

`scripts/predecir.py`

**Archivo de dependencias:**

`requirements-phase2-lock.txt`

#### Ejecución

Desde `dbt_red_metropolitana`:

```bash
python scripts/predecir.py --datos . --fecha-corte 2026-08-30
```

El script carga el modelo guardado y genera las predicciones del corte C sin volver a entrenarlo.


#### Ejecución desde la raíz del repositorio

También se verificó la ejecución desde la carpeta principal
del repositorio, utilizando el siguiente comando:

    python dbt_red_metropolitana/scripts/predecir.py --datos dbt_red_metropolitana --fecha-corte 2026-08-30

La ejecución procesó 57,925 usuarios, generó 6,385
selecciones para contacto y produjo el archivo:

`outputs/churn/predictions_C_phase2.csv`

El modelo fue cargado desde el artefacto versionado y
no se realizó un nuevo entrenamiento.

#### Resultados

- Usuarios procesados: 57,925.
- Usuarios con tarjeta respaldada por CDC: 27,200.
- Usuarios sin tarjeta recuperada: 30,725.
- Usuarios seleccionados para contacto: 6,385.

El CSV contiene:

`unidad_id, tarjetas, puntaje, contactar`

#### Validaciones

Se verificó que:

- No existieran identificadores duplicados en el CSV final.
- No existieran puntajes nulos.
- Los puntajes estuvieran entre 0 y 1.
- El pipeline reprodujera las probabilidades del clasificador original.
- Las auditorías de características de A, B y C no presentaran diferencias.

La comparación de predicciones del corte C mostró una diferencia máxima de aproximadamente `2.22 × 10⁻¹⁶`, sin diferencias superiores a `1e-12`.

#### Respaldo de tarjetas

La verificación de asociaciones obtuvo:

| Resultado | Cantidad |
|---|---:|
| Asociaciones totales | 67,040 |
| Asociaciones respaldadas por CDC | 27,200 |
| Asociaciones sin respaldo | 39,840 |
| Usuarios distintos con tarjeta respaldada | 27,200 |

Se utilizaron registros del padrón anteriores al corte C.

La dimensión de identidad no se reconstruyó completamente como una fotografía histórica de cada fecha, por lo que este aspecto permanece como una limitación metodológica.


#### Auditoría de cobertura de tarjetas del corte C

Se realizó una auditoría adicional para explicar las 30,725
unidades que aparecen sin tarjeta en el archivo final.

| Categoría | Usuarios | Porcentaje |
|---|---:|---:|
| Sin identidad Transmetro/Transurbano | 12,588 | 21.73% |
| Identidad TM/TU sin coincidencia CDC | 18,137 | 31.31% |
| Coincidencia CDC únicamente posterior al corte | 0 | 0.00% |
| Tarjeta válida al corte | 27,200 | 46.96% |
| **Total** | **57,925** | **100.00%** |

La auditoría permitió identificar que las 30,725 unidades sin
tarjeta recuperable corresponden a dos situaciones:

- 12,588 no tienen identidad de Transmetro o Transurbano.
- 18,137 tienen identidad de esos modos, pero no presentan
  coincidencia en el padrón CDC.

No se encontraron coincidencias CDC exclusivamente posteriores
a la fecha de corte.

Por lo tanto, se conservaron las restricciones temporales
y no se asignaron identificadores artificiales.

Las 57,925 unidades mantienen su predicción de abandono,
aunque únicamente 27,200 cuentan con tarjeta recuperable
mediante la relación auditada.

Los 6,385 usuarios seleccionados por el modelo representan
candidatos para una campaña, no necesariamente contactos
ejecutables. La contactabilidad efectiva depende de los
identificadores disponibles y de los canales autorizados.

Evidencia:

`docs/churn/card_identity_audit_C.md`

### 7. Limitaciones

El proyecto presenta las siguientes limitaciones:

- Random Forest muestra cierto sobreajuste.
- La mejora frente a regresión logística es pequeña.
- La ganancia económica es estimada y depende de los supuestos utilizados.
- El corte B ya había sido examinado durante la fase anterior.
- No todos los usuarios cuentan con una tarjeta recuperable.
- La conformación histórica de identidades no fue auditada de forma integral.
- El corte C todavía no dispone de etiquetas para comprobar el abandono real.
- Los identificadores de tarjetas deben protegerse y no publicarse innecesariamente.

### 8. Conclusiones

La Fase 02 permitió ampliar el análisis de abandono con un modelo Ensemble, una política económica de contacto y una segmentación de usuarios.

Random Forest obtuvo un rendimiento ligeramente superior al de regresión logística, aunque presentó mayor diferencia entre entrenamiento y validación.

La política de contacto produjo una ganancia estimada positiva tanto en A como en B.

La segmentación identificó dos grupos con comportamientos y tasas de abandono diferentes, lo que permite proponer intervenciones específicas.

Finalmente, se preparó un pipeline versionado que genera predicciones para el corte C sin reentrenamiento.

El sistema constituye una base reproducible para apoyar campañas de retención, aunque requiere seguimiento con resultados reales y mejoras en la trazabilidad histórica de identidades.

## Reproducibilidad y entrega de predicciones

### Ejecución del predictor

El archivo `predecir.py` ubicado en la raíz del repositorio
permite ejecutar el predictor de la Fase 02.

Comando oficial:

    python predecir.py --datos datos_red --fecha-corte 2026-08-30

También se verificó:

    python predecir.py --datos dbt_red_metropolitana --fecha-corte 2026-08-30

Ambos comandos finalizaron correctamente.

Las características se consultan desde la tabla
`churn.churn_features` de PostgreSQL. El argumento `--datos`
no carga directamente los archivos de la carpeta indicada.

### Modelo utilizado

- Algoritmo: Random Forest.
- Artefacto: `churn_pipeline_v1.joblib`.
- Corte de entrenamiento: A.
- Umbral de contacto: 0.333333.
- Predicción sin reentrenamiento.

### Resultados del corte C

| Indicador | Resultado |
|---|---:|
| Fecha de corte | 2026-08-30 |
| Usuarios procesados | 57,925 |
| Usuarios con tarjeta | 27,200 |
| Usuarios sin tarjeta | 30,725 |
| Usuarios a contactar | 6,385 |

### Archivo oficial

Ruta: `dbt_red_metropolitana/outputs/churn/predictions_C_phase2.csv`

Columnas: `unidad_id,tarjetas,puntaje,contactar`

El archivo contiene 57,925 filas, una por usuario del corte C.

Los identificadores múltiples de tarjeta se separan mediante
punto y coma.

Los datos son simulados y corresponden al Proyecto 02
de Ciencia de Datos de la Universidad Rafael Landívar.

El archivo CSV completo se incluye en la entrega de GitHub.
