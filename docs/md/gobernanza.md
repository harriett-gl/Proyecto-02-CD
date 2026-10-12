# Gobernanza de datos — Agencia Metropolitana de Transporte

Este documento fija las reglas que los cuatro operadores comparten en el warehouse
(sección 3.1). Complementa el [diccionario de datos](diccionario_datos.md) y el

## 1. Definiciones oficiales

| Término | Definición oficial | Dónde se implementa |
|---|---|---|
| **Abordaje** | Un acceso válido de un usuario a un modo: validación de Transmetro sin duplicar, transacción **aprobada** de Transurbano (estado 1, 2 o 3), abordaje de Aerómetro o entrada a MetroRiel. | `gold.fct_abordajes`, `gold.rpt_demanda_red` |
| **Viaje** | Para la Agencia, **un viaje = un abordaje válido**. En MetroRiel un viaje es el trayecto completo con entrada y salida; cuenta una sola vez, en su estación y hora de **entrada**. No se infiere el viaje puerta a puerta. | `gold.rpt_demanda_red` |
| **Viajes del mes** | Suma de `abordajes` de `gold.rpt_demanda_red` cuyo `fecha_sk` cae en el mes calendario (hora local de Guatemala). Ver consulta oficial abajo. | `gold.rpt_demanda_red` |
| **Transacción rechazada** | Transurbano con estado 7 (saldo insuficiente) o 9 (tarjeta inválida). Es un evento válido, **no** un abordaje: queda en Silver y no entra a Gold. | `silver.transurbano_transacciones` |
| **Usuario activo (padrón)** | Tarjeta del padrón de Transmetro cuya **última** operación CDC, en orden de `seq`, no es `DELETE`. | `silver.dim_usuario_actual.activo` |
| **Usuario activo (operación)** | Usuario con al menos un abordaje válido en los 30 días previos a la fecha de corte. | `features.features_usuario_movilidad.viajes_ultimos_30d > 0` |
| **Usuario multimodal** | Usuario (`usuario_sk`) identificado en dos o más modos (por viajes o por padrón). Cifra oficial del tablero: **36,829**. La tabla de features cuenta solo viajes observados y da 36,827: la diferencia son 2 usuarios que aparecen en Transmetro solo por el padrón, sin viajes. | `gold.dim_usuario.cantidad_modos_identificados >= 2` |
| **Hora pico** | 06:00–08:59 y 16:00–18:59, hora local. Una sola macro (`es_hora_pico`) la usan Gold y Features. | `macros/definiciones_oficiales.sql` |
| **Zona** | Zona municipal (`Zona N`) o municipio. `Z10`, `ZONA 10`, `Zona 10` y `district` apuntan a la misma zona (macro `normalizar_zona`). | `silver.dim_zona_conformada` |
| **Zona sin servicio** | Zona donde residen usuarios del padrón pero ningún modo registró actividad. | `gold.rpt_cobertura_zona.sin_servicio` |
| **Registro inválido** | Registro que incumple una regla de calidad (tabla de la sección 4). Nunca se borra: va a cuarentena con su motivo. | esquema `quarantine` |

### Prueba de fuego: "viajes del mes"

Cualquier integrante que calcule los viajes de un mes debe usar esta consulta y
obtener el mismo número:

```sql
SELECT LEFT(fecha_sk::text, 6) AS mes, SUM(abordajes) AS viajes
FROM gold.rpt_demanda_red
GROUP BY 1
ORDER BY 1;
```

Resultado medido: **junio 2026 = 1,093,235 viajes** · **julio 2026 (1 al 15) = 554,334 viajes**.
La prueba dbt `tests/conciliacion_silver_gold.sql` verifica en cada corrida que
el mismo conteo calculado desde Silver y desde Gold coincida por modo.

## 2. Dueño por dominio

| Dimensión / dominio | Dueño (autoriza cambios) | Ejemplo de cambio que debe autorizar |
|---|---|---|
| `dim_zona` y normalización de zonas | Dirección de Planificación Territorial | Crear una zona nueva, cambiar a qué zona pertenece una estación |
| `dim_modo` | Gerencia de Operaciones | Incorporar un quinto modo |
| `dim_fecha`, `dim_hora`, definición de hora pico | Equipo de Datos de la Agencia | Cambiar el rango de hora pico |
| `dim_usuario`, estrategia de identidad y seudonimización | Gobernanza y Seguridad de la Información | Cambiar la regla que une tarjetas entre operadores |
| `fct_abordajes`, `fct_viajes_metroriel` | Gerencia de Operaciones | Cambiar qué cuenta como abordaje |
| `features_usuario_movilidad` | Equipo de Ciencia de Datos | Agregar o cambiar una feature, mover la fecha de corte |

**Si mañana cambia la definición de zona**, la propone el equipo de datos, la
autoriza Planificación Territorial y se cambia en un solo lugar
(`macros/definiciones_oficiales.sql`), con commit y nueva corrida del flujo.

## 3. Linaje

- Versión interactiva: `dbt docs generate` + `dbt docs serve` (carpeta `dbt_red_metropolitana`).
- Cada tabla de staging declara en `models/staging/sources.yml` su **archivo crudo**
  (`datos_red/...`) y su carpeta **Bronze**; el tablero está declarado como
  *exposure* en `models/exposures.yml`. Así, cualquier métrica del tablero se
  rastrea: tablero → Gold → Silver → staging → Bronze (Parquet) → archivo crudo.
- En Bronze cada fila conserva `_source_file`, `_ingestion_ts` y, en streaming,
  `_kafka_offset`; Silver conserva `archivo_origen` y `fecha_ingesta`.

## 4. Reglas de calidad (definidas antes del código)

| Regla | Fuente | Qué se considera inválido | Qué se hace | Tabla de cuarentena | Registros |
|---|---|---|---|---|---:|
| Duplicado de torniquete | Transmetro | Mismo `validacion_id` leído más de una vez | Se conserva la primera lectura (menor offset Kafka) | `transmetro_duplicados` | 1,115 |
| Código de parada nulo | Transurbano | `cod_parada` vacío | No se puede ubicar en una zona | `transurbano_invalidos` | 4,186 |
| Fecha futura | Transurbano | Fecha del viaje posterior a la fecha de ingesta | Reloj de la unidad mal configurado | `transurbano_invalidos` | 814 |
| Parada nula y fecha futura | Transurbano | Ambas reglas | Ambos motivos en `motivo_rechazo` | `transurbano_invalidos` | 3 |
| Viaje sin salida | MetroRiel | `exit` nulo o sin duración | El pasajero no validó la salida | `metroriel_sin_salida` | 3,589 |
| Duplicado / estación desconocida | Aerómetro | `boarding_id` repetido o estación fuera del catálogo | Se aísla | `aerometro_invalidos` | 0 |
| Llave ausente | CDC padrón | `tarjeta = 'SIN-TARJETA'` | Se aísla | `cdc_llaves_invalidas` | 2,206 |
| Llave de otro operador | CDC padrón | Tarjeta que no tiene formato `TC-########` | El padrón se define como de Transmetro | `cdc_llaves_invalidas` | 6,518 |
| **Total** | | | | | **18,431** |

Ningún registro se descarta en silencio: la prueba
`tests/cuarentena_cuadra_con_staging.sql` comprueba en cada corrida que
*filas en staging = filas en Silver + filas en cuarentena* para cada fuente.
