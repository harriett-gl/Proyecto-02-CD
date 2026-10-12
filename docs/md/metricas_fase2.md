# Métricas — Fase 02

Cifras medidas sobre una corrida completa del flujo (`../../orchestration/flow_red_metropolitana.py`)
con los datos de `generar_red_metropolitana.py` (semilla 2026, escala 0.08). Las métricas de
la Fase 01 siguen en [metricas_fase1.md](metricas_fase1.md).

## Idempotencia (verificación previa a la presentación)

Base de datos vacía, `../../lake` vacío, tres corridas consecutivas:

| Corrida | Estado | Staging | Silver | Gold | Cuarentena | Pruebas dbt |
|---|---|---:|---:|---:|---:|---|
| 1 | EXITOSA | 1,730,184 | 1,919,885 | 1,718,037 | 18,431 | 180 PASS, 0 ERROR |
| 2 | EXITOSA | 1,730,184 | 1,919,885 | 1,718,037 | 18,431 | 180 PASS, 0 ERROR |
| 3 | EXITOSA | 1,730,184 | 1,919,885 | 1,718,037 | 18,431 | 180 PASS, 0 ERROR |

En la segunda y tercera corrida la ingesta batch y CDC omitió los archivos ya
procesados (hash SHA-256 en el manifiesto) y el consumidor Kafka descartó los
363,221 + 203,554 eventos repetidos (control de ocurrencias en SQLite): Bronze no
creció. Las vistas nuevas de la Fase 02 (`rpt_*`) no son tablas, por lo que los
conteos de Gold coinciden con los de la Fase 01.

> Nota: la evidencia de Fase 01 registró 1,919,887 filas en Silver; una base de datos
> limpia produce 1,919,885 (2 filas de diferencia, probablemente una tabla de una
> versión anterior que quedó en el esquema). Staging, Gold y Cuarentena coinciden exactamente.

## Cobertura

| Métrica | Valor |
|---|---:|
| Zonas con servicio (al menos un modo) | 15 |
| Zonas sin servicio | 1 — Santa Catarina Pinula (946 residentes activos) |
| Zonas con los 4 modos | 3 — Zona 17, Zona 12, Zona 1 |
| Zonas con solo 2 modos | 4 — Zona 4, 9, 10 y 11 |
| Usuarios multimodales (tablero, `dim_usuario`) | 36,829 de 70,380 (52.3 %) |
| Usuarios en 2 modos / 3 modos | 26,833 / 9,996 |

## Features

| Métrica | Valor |
|---|---:|
| Filas (usuarios) en `features.features_usuario_movilidad` | 70,380 |
| Fecha de corte | 2026-07-15 |
| Columnas | 24 |
| Tamaño en disco | 17 MB |

## Rendimiento

### Duración por etapa (corrida 3)

| Etapa | Duración |
|---|---:|
| Ingesta Bronze | 15.5 s |
| Carga Staging | 12.9 s |
| dbt build (31 modelos + 149 pruebas) | 65.2 s |
| Auditoría | 0.4 s |
| Limpieza de Staging | 0.3 s |
| **Total** | **94.4 s** |

### Tiempo de las consultas del tablero

Medido con `python scripts/medir_consultas_tablero.py` (mediana de 5 ejecuciones):

| Consulta | Mediana |
|---|---:|
| Demanda por modo (4 modos, vista `rpt_demanda_red`) | 3,566 ms |
| Demanda por zona | 177 ms |
| Demanda por hora | 395 ms |
| Usuarios multimodales | 9 ms |
| Viajes por estación MetroRiel | 63 ms |
| Cobertura por zona | 341 ms |
| Caso MetroRiel (ranking) | 253 ms |

La consulta más lenta es la de los 4 modos porque la vista agrega 1.6 millones de
filas en cada consulta; en Tableau conviene usar un extracto para esa fuente.

### Tamaño en disco por capa

| Capa | Tamaño |
|---|---:|
| Bronze (Parquet) | 68 MB |
| Staging (vacío al terminar) | 72 kB |
| Silver | 277 MB |
| Quarantine | 3.4 MB |
| Gold | 381 MB |
| Features | 17 MB |
| Audit | 32 kB |
