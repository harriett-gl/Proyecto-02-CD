# 🚇 Proyecto 02 — Red Metropolitana
## Predicción de abandono de usuarios del transporte público

**Universidad:** Rafael Landívar
**Curso:** Ciencia de Datos
**Proyecto:** ¿Quién deja de usar la red?
**Fases:** Fase 01 — Modelado inicial | Fase 02 — Modelado avanzado y producción

### 👩‍💻 Integrantes
- Harriett Guzmán
- Susana García
- Rochelle Esquivel

---

## 📌 1. Descripción general

El Proyecto 02 tiene como objetivo identificar a los usuarios de la Red Metropolitana que presentan mayor probabilidad de dejar de utilizar el transporte público.

Para ello, se integran datos de cuatro operadores:

- Transmetro
- Transurbano
- MetroRiel
- Aerómetro

El proyecto utiliza técnicas de ingeniería de datos, aprendizaje automático y evaluación temporal para desarrollar modelos predictivos de abandono (*churn*).

Se reutiliza la infraestructura de ingesta y transformación del Proyecto 01, incorporando nuevos modelos analíticos y predictivos específicos para el Proyecto 02.

## 🎯 2. Objetivos

**Objetivo general**

Desarrollar un sistema predictivo que permita identificar usuarios con riesgo de abandono y apoyar estrategias de retención y reactivación.

**Objetivos específicos**

- Integrar y validar información de movilidad de diferentes operadores.
- Definir una población elegible y una etiqueta de abandono.
- Construir características predictivas sin fuga temporal.
- Comparar modelos baseline con modelos de clasificación.
- Evaluar el rendimiento mediante validación cruzada y cortes temporales.
- Analizar el costo y beneficio de contactar usuarios.
- Identificar segmentos de movilidad.
- Preparar un pipeline reproducible para predicciones.

---

## 🏗️ 3. Arquitectura del proyecto

El procesamiento utiliza las siguientes capas:

```text
FUENTES ORIGINALES
        |
        v
INGESTA BATCH / STREAMING / CDC
        |
        v
BRONZE
        |
        v
STAGING
        |
        v
SILVER
        |
        v
CHURN_VALID_TRIPS
        |
        +----> CHURN_POPULATION_LABELS
        |
        +----> CHURN_FEATURES
                      |
                      v
               MODELOS DE ML
                      |
             +--------+--------+
             |                 |
             v                 v
       REGRESIÓN           RANDOM
       LOGÍSTICA           FOREST
             |                 |
             +--------+--------+
                      |
                      v
               EVALUACIÓN
                      |
                      v
              PREDICCIONES
```

Las características del modelo se construyen a partir de Silver, sin depender de las tablas de hechos de Gold.

---

## 🛠️ 4. Tecnologías utilizadas

| Tecnología | Función |
|---|---|
| Python | Ingesta, procesamiento y modelado |
| PostgreSQL | Almacenamiento de datos |
| Docker | Contenedores |
| Apache Kafka | Procesamiento de eventos |
| dbt Core | Transformaciones y pruebas |
| Pandas | Manipulación de datos |
| Scikit-learn | Modelos de aprendizaje automático |
| PyArrow | Archivos Parquet |
| Joblib | Serialización de modelos |
| Git y GitHub | Control de versiones |

---

# 🟣 FASE 01 — Preparación de datos y modelado inicial

## 5. Integración y validación de datos

Se integraron nueve fuentes correspondientes a los operadores de transporte y sus catálogos.

**Resultados de reconciliación:**

| Fuente | Registros |
|---|---:|
| Estaciones Transmetro | 104 |
| Paradas Transurbano | 328 |
| Estaciones MetroRiel | 22 |
| Estaciones Aerómetro | 14 |
| Transacciones Transurbano | 1,635,788 |
| Viajes MetroRiel | 590,844 |
| Padrón CDC | 77,636 |
| Validaciones Transmetro | 713,786 |
| Abordajes Aerómetro | 387,053 |
| **Total** | **3,405,575** |

La reconciliación entre las fuentes y los registros cargados no presentó diferencias.

## 6. Unidad de análisis y definición de churn

La unidad de análisis seleccionada es el usuario conformado, identificado mediante `usuario_sk`.

**Reglas utilizadas:**

- Elegibilidad: al menos dos viajes válidos en los 28 días anteriores al corte.
- Churn = 1: el usuario no registra viajes durante los 30 días posteriores.
- Churn = 0: el usuario registra al menos un viaje durante ese período.
- El corte C se utiliza para predicción sin etiqueta conocida.

### Cortes temporales

| Corte | Fecha | Usuarios | Churn |
|---|---|---:|---:|
| A | 2026-07-01 | 59,796 | 7,396 (12.37%) |
| B | 2026-07-31 | 58,372 | 6,671 (11.43%) |
| C | 2026-08-30 | 57,925 | Sin etiqueta |

## 7. Limitaciones de identidad

Se identificaron 145,561 registros de identidad y 93,009 usuarios conformados distintos.

Además, 42,854 usuarios fueron identificados en varios modos de transporte.

Los identificadores conformados no garantizan una correspondencia exacta con personas físicas.

En el corte A se reportaron 1,468 casos positivos asociados a usuarios aislados de Aerómetro, respecto de 7,396 casos positivos totales.

La proporción es:

**1,468 / 7,396 × 100 = 19.85%**

Esta cifra evidencia una limitación en la vinculación de identidades y debe interpretarse considerando las reglas de conformación de usuarios.

## 8. Ingeniería de características

Se construyeron 14 variables predictivas:

| Característica | Descripción |
|---|---|
| `trips_28d` | Viajes de los últimos 28 días |
| `trips_7d` | Viajes de los últimos 7 días |
| `active_days_28d` | Días con actividad |
| `days_since_last_trip` | Días desde el último viaje |
| `transport_modes_count` | Cantidad de modos utilizados |
| `is_multimodal` | Indicador multimodal |
| `transmetro_trips` | Viajes en Transmetro |
| `transurbano_trips` | Viajes en Transurbano |
| `metroriel_trips` | Viajes en MetroRiel |
| `aerometro_trips` | Viajes en Aerómetro |
| `weekend_trip_ratio` | Proporción de viajes de fin de semana |
| `peak_hour_trip_ratio` | Proporción de viajes en horario pico |
| `total_spending_gtq` | Gasto total en quetzales |
| `average_spending_gtq` | Gasto promedio en quetzales |

Las características se calculan utilizando únicamente información disponible antes de cada fecha de corte.

## 9. Prevención de fuga temporal

Se implementaron auditorías para comprobar que los modelos no utilizaran información futura.

La comparación entre datos originales y datos temporalmente recortados produjo:

- Corte A: 0 diferencias.
- Corte B: 0 diferencias.
- Corte C: 0 diferencias.

**Resultado: PASS.**

## 10. Entrenamiento y comparación de modelos

El entrenamiento inicial se realizó exclusivamente con el corte A.

Se utilizó validación cruzada estratificada de cinco particiones y semilla aleatoria 42.

| Modelo | PR-AUC promedio | Desviación estándar |
|---|---:|---:|
| Baseline constante | 0.123687 | 0.000029 |
| Baseline frecuencia | 0.262542 | 0.004275 |
| Regresión logística L1 | 0.428200 | 0.014151 |
| Regresión logística L2 | 0.429148 | 0.014108 |

**Modelo seleccionado: regresión logística L2, con C = 0.001.**

La regresión logística L2 presentó el mejor PR-AUC promedio de los modelos iniciales.

## 11. Evaluación temporal

El corte B se utilizó para evaluar temporalmente el modelo entrenado con A.

No se utilizó B para entrenar el modelo inicial ni para seleccionar sus hiperparámetros.

El corte C se mantuvo sin etiqueta y se reservó para generar predicciones.

## 12. Resultados de la Fase 01

- 9 fuentes reconciliadas.
- 3,405,575 registros integrados.
- 14 características predictivas.
- 59,796 usuarios elegibles en A.
- 7,396 usuarios con churn en A.
- Regresión logística L2 seleccionada.
- PR-AUC promedio de 0.429148.
- Auditorías temporales aprobadas.
- 13 pruebas dbt de churn aprobadas.

---

# 🔵 FASE 02 — Modelado avanzado y producción

## 13. Modelos Ensemble

Se incorporó Random Forest para comparar su comportamiento con la regresión logística.

El modelo se evaluó utilizando los mismos cinco folds de validación.

**Resultados:**

| Métrica | Resultado |
|---|---:|
| PR-AUC entrenamiento | 0.5001 |
| PR-AUC validación | 0.4352 |
| Brecha entrenamiento-validación | 0.0649 |

Se utilizó importancia por permutación en validación para interpretar la contribución de las características.

La variable más importante fue `days_since_last_trip`.

## 14. Optimización del umbral

Se utilizó un criterio económico para decidir qué usuarios contactar.

**Parámetros:**

- Costo por contacto: Q5.
- Beneficio esperado por retención: Q60.
- Probabilidad de éxito de la intervención: 25%.

Umbral económico teórico:

**5 / (0.25 × 60) = 0.333333**

La evaluación reportó:

- Ganancia estimada en A: Q12,715.
- PR-AUC temporal en B: 0.3995.
- Ganancia estimada en B: Q9,305.

El corte B se utilizó para evaluación temporal, no para modificar el umbral después de observar sus resultados.

## 15. Segmentación de usuarios

Se aplicaron técnicas de KMeans y PCA para identificar grupos de comportamiento.

Se seleccionaron dos segmentos.

| Segmento | Proporción | Churn observado | Acción |
|---|---:|---:|---|
| 0 | 81.9% | 14.7% | Reactivación |
| 1 | 18.1% | 1.9% | Fidelización |

El PCA bidimensional explicó aproximadamente el 47.54% de la varianza.

## 16. Pipeline predictivo

Se preparó un pipeline que incorpora tratamiento de valores faltantes y clasificación.

El modelo serializado se encuentra en:

`dbt_red_metropolitana/outputs/churn/models/churn_pipeline_v1.joblib`

El proceso de predicción está diseñado para recibir una fecha de corte, calcular puntajes y determinar qué usuarios contactar.

**Estado:** la interfaz de ejecución y la exportación oficial del corte C están pendientes de las correcciones identificadas en la auditoría técnica.

## 17. Auditoría de invariancia temporal

Se comprobó que la incorporación de eventos posteriores al corte C no alterara las predicciones correspondientes a ese corte.

Resultados reportados:

- Predicciones comparadas: 57,925.
- Diferencias de clasificación: 0.
- Diferencia máxima de probabilidad: aproximadamente 3.33 × 10⁻¹⁶.

**Resultado: PASS.**

---

# ⚙️ 18. Instalación y ejecución

## Requisitos

- Python y dependencias del proyecto.
- Docker Desktop.
- PostgreSQL.
- Apache Kafka.
- dbt Core y dbt-postgres.

## Preparación

Desde la raíz del repositorio:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Configurar las variables de entorno:

```bash
cp .env.example .env
```

Editar `.env` con las credenciales de PostgreSQL y una clave `USUARIO_SALT` segura.

No subir `.env` a GitHub.

## Levantar los servicios

```bash
docker compose up -d
docker compose ps
```

## Validar los datos

Desde `dbt_red_metropolitana`:

```bash
python scripts/run_pipeline_p2.py --mode validate
```

## Ejecutar los modelos de churn

```bash
dbt run --select +churn_features --profiles-dir .
dbt test --select churn_population_labels churn_features --profiles-dir .
```

Estos comandos pueden modificar tablas en la base de datos configurada.

## Auditoría temporal

```bash
python scripts/audit_temporal_leakage.py
```

## Entrenamiento inicial

```bash
python scripts/train_churn.py
```

## Reconstrucción independiente

El script `run_pipeline_p2.py` incluye el modo `rebuild-dbt`, que permite reconstruir el pipeline utilizando un entorno de pruebas aislado.

Antes de ejecutarlo, deben comprobarse las variables de conexión y las rutas de los directorios Bronze.

---

# 📁 19. Documentación y evidencias

La documentación de churn se encuentra en:

- `dbt_red_metropolitana/docs/churn/phase1_completion.md`
- `dbt_red_metropolitana/docs/churn/feature_dictionary.md`
- `dbt_red_metropolitana/docs/churn/model_evaluation.md`
- `dbt_red_metropolitana/docs/churn/model_card_phase2.md`
- `dbt_red_metropolitana/docs/churn/evaluation_log.md`

Entre los artefactos de evaluación se incluyen:

- `dbt_red_metropolitana/outputs/churn/regularization_curve_A.png`
- `dbt_red_metropolitana/outputs/churn/evidencias/pipeline_timings.csv`

---

# 🔐 20. Seguridad y reproducibilidad

El proyecto contempla:

- Uso de variables de entorno para credenciales.
- Seudonimización de usuarios mediante HMAC-SHA256.
- Separación de capas de procesamiento.
- Validaciones automatizadas con dbt.
- Auditorías de fuga temporal.
- Evaluación con cortes temporales.
- Registro de métricas y evidencias.
- Reconstrucción en entornos aislados.

---

# 📚 21. Conclusiones

La Fase 01 permitió construir una base de datos validada, definir el problema de abandono y desarrollar modelos iniciales de clasificación.

La regresión logística L2 obtuvo el mejor rendimiento entre los modelos iniciales evaluados.

La Fase 02 amplió el análisis mediante Random Forest, optimización económica del umbral, segmentación de usuarios y preparación de un pipeline predictivo.

El proyecto permite estudiar el riesgo de abandono y apoyar decisiones relacionadas con la retención de usuarios de la Red Metropolitana.

---

**Universidad Rafael Landívar — Ciencia de Datos — Proyecto 02**
