# Proyecto 02 — Fase 01
## Complemento de evidencias técnicas

### 1.1 Reconciliación de fuentes

Se procesaron nueve archivos de entrada mediante el pipeline
reproducible de ingesta y transformación.

| Fuente | Registros | Diferencia |
|---|---:|---:|
| tm_estaciones.csv | 104 | 0 |
| tu_paradas.csv | 328 | 0 |
| mr_estaciones.csv | 22 | 0 |
| am_estaciones.csv | 14 | 0 |
| transurbano_transacciones.csv | 1,635,788 | 0 |
| metroriel_viajes.jsonl | 590,844 | 0 |
| cdc_padron_usuarios.csv | 77,636 | 0 |
| transmetro_validaciones.csv | 713,786 | 0 |
| aerometro_boardings.csv | 387,053 | 0 |
| **Total** | **3,405,575** | **0** |

La comparación entre los archivos originales y la capa Bronze
no detectó diferencias en el número de registros.

La reconstrucción aislada ejecutada anteriormente tuvo una
duración total de 188.49 segundos, con 33 modelos dbt y
128 pruebas satisfactorias.

### 1.2 Unidad de análisis y etiquetas

La unidad de análisis es el identificador de usuario
seudonimizado `usuario_sk`.

Se considera elegible a un usuario con al menos dos viajes
durante los 28 días anteriores a la fecha de corte.

La etiqueta de abandono es igual a 1 cuando no se registran
viajes durante los 30 días posteriores al corte; en caso
contrario, es 0.

| Corte | Fecha | Usuarios | Abandono |
|---|---|---:|---:|
| A | 2026-07-01 | 59,796 | 7,396 (12.37%) |
| B | 2026-07-31 | 58,372 | 6,671 (11.43%) |
| C | 2026-08-30 | 57,925 | Sin etiqueta |

#### Costo de identidad y limitaciones

La dimensión Silver contiene 145,561 registros de identidad
asociados con 93,009 usuarios conformados distintos.

La diferencia es de 52,552 registros adicionales respecto
al número de usuarios únicos conformados. Además, 42,854
usuarios aparecen identificados en más de un modo de transporte.

Aerómetro registra 16,930 identificadores, todos distintos
dentro de ese modo.

Estos resultados permiten cuantificar la multiplicidad de
identificadores, pero no equivalen necesariamente al número
real de personas. Una persona puede utilizar varias tarjetas
y pueden existir vínculos no identificados entre operadores.

Por tanto, el análisis de abandono se realiza sobre
identidades conformadas (usuario_sk), no sobre personas
físicas verificadas. Esta limitación puede afectar la
estimación de usuarios y las tasas de abandono.

### 1.3 Características y fuga temporal

Se construyeron 14 características predictivas utilizando
los 28 días anteriores a cada fecha de corte.

La auditoría temporal del corte A comparó las características
originales contra las recalculadas con viajes recortados
antes de la fecha de corte.

- Usuarios originales: 59,796.
- Usuarios recalculados: 59,796.
- Usuarios con diferencias: 0.
- Resultado: PASS.

El diccionario detallado se encuentra en
`docs/churn/feature_dictionary.md`.

**Migración a Silver validada:** los modelos de población y
características utilizan `churn_valid_trips`, construido
directamente desde las cuatro fuentes Silver.

La comparación contra los respaldos anteriores confirmó:

- Población total: 176,093 registros.
- Diferencias de población y etiquetas: 0.
- Diferencias de características: 0.
- Pruebas dbt de churn: 13 PASS, 0 WARN, 0 ERROR.

### 1.4 Comparación de modelos

El entrenamiento utilizó únicamente el corte A, con
validación cruzada estratificada de cinco particiones
y semilla aleatoria 42.

| Modelo | PR-AUC promedio | Desviación estándar |
|---|---:|---:|
| Baseline constante | 0.123687 | 0.000029 |
| Baseline frecuencia | 0.262542 | 0.004275 |
| Regresión logística L1 | 0.428200 | 0.014151 |
| Regresión logística L2 | 0.429148 | 0.014108 |

El mejor modelo según PR-AUC fue la regresión logística
L2 con C = 0.001.

#### Interpretación de cinco coeficientes positivos

Los coeficientes corresponden a variables estandarizadas.
Un coeficiente positivo indica una asociación con mayores
log-odds estimados de abandono, manteniendo constantes las
demás características.

1. **days_since_last_trip (+0.649837):**
   cuanto más tiempo transcurre desde el último viaje,
   mayor es el riesgo estimado de abandono.

2. **metroriel_trips (+0.034831):**
   presenta una asociación positiva pequeña con el abandono.

3. **weekend_trip_ratio (+0.032439):**
   una mayor proporción de viajes en fin de semana
   se relaciona con un ligero aumento del riesgo estimado.

4. **transmetro_trips (+0.023573):**
   presenta una asociación positiva pequeña,
   considerando simultáneamente las demás variables.

5. **peak_hour_trip_ratio (+0.021246):**
   una mayor proporción de viajes en horario pico
   muestra una asociación positiva pequeña.

Estas asociaciones no demuestran causalidad.

La gráfica de regularización se encuentra en
`outputs/churn/regularization_curve_A.png`.

El corte B no se utilizó para entrenar ni seleccionar
el modelo de la Fase 01.
