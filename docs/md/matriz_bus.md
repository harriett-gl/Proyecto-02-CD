# Matriz del bus - Red Metropolitana

## Grano de las tablas de hechos

### gold.fct_abordajes

Una fila representa un abordaje válido realizado por un usuario en Transmetro, Transurbano o Aerómetro, en una ubicación y fecha-hora determinadas.

Las transacciones rechazadas de Transurbano no se consideran abordajes.

### gold.fct_viajes_metroriel

Una fila representa un viaje completo y válido de MetroRiel, desde una estación de entrada hasta una estación de salida.

MetroRiel se conserva en una tabla separada porque registra origen, destino y duración, mientras que los otros operadores solamente registran abordajes.

## Matriz del bus

| Proceso | Fecha | Hora entrada o abordaje | Hora salida | Usuario | Modo | Zona origen | Zona destino | Ubicación o estación | Servicio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Abordajes de Transmetro, Transurbano y Aerómetro | X | X |  | X | X | X |  | X | X |
| Viajes completos de MetroRiel | X | X | X | X | X | X | X | X |  |

## Tablas de hechos

### gold.fct_abordajes

Medidas:

- `cantidad_abordajes`
- `monto_gtq`

Dimensiones relacionadas:

- `gold.dim_fecha`
- `gold.dim_hora`
- `gold.dim_usuario`
- `gold.dim_modo`
- `gold.dim_zona`

### gold.fct_viajes_metroriel

Medidas:

- `cantidad_viajes`
- `monto_gtq`
- `duracion_segundos`

Dimensiones relacionadas:

- `gold.dim_fecha`
- `gold.dim_hora`
- `gold.dim_usuario`
- `gold.dim_modo`
- `gold.dim_zona`

## Dimensiones conformadas

- `gold.dim_fecha`: calendario común para todos los operadores.
- `gold.dim_hora`: hora del día, franja horaria y clasificación de hora pico.
- `gold.dim_usuario`: usuario seudonimizado e identidad aproximada entre operadores.
- `gold.dim_modo`: catálogo de los cuatro modos de transporte.
- `gold.dim_zona`: nombres de zona normalizados.

Los campos `ubicacion_codigo` y `servicio` se mantienen como dimensiones degeneradas dentro de la tabla de abordajes debido a que cada operador utiliza catálogos y códigos diferentes.

## Clasificación de medidas

| Medida | Clasificación | Justificación |
|---|---|---|
| `cantidad_abordajes` | Aditiva | Puede sumarse por fecha, modo, hora y zona. |
| `monto_gtq` | Aditiva | Puede sumarse para calcular ingresos por cualquier dimensión. |
| `cantidad_viajes` | Aditiva | Puede sumarse entre fechas, usuarios y estaciones. |
| `duracion_segundos` | Aditiva | Puede sumarse para obtener el tiempo total acumulado de viaje. |
| Tarjetas activas a una fecha de corte | Semi-aditiva | Puede sumarse entre zonas, pero no entre fechas porque duplicaría el saldo de usuarios. |
| Promedio de gasto por viaje | No aditiva | Debe recalcularse dividiendo el monto total entre la cantidad de viajes. |
| Usuarios distintos | No aditiva | Un mismo usuario puede aparecer en varias zonas, fechas y modos. |

## Decisiones de diseño

1. Se eligió el abordaje como grano principal porque Transmetro, Transurbano y Aerómetro registran eventos individuales de entrada.

2. Los viajes de MetroRiel se almacenan en otra tabla de hechos porque incluyen entrada, salida y duración.

3. Gold solamente lee modelos de Silver mediante referencias de dbt; nunca accede directamente a Bronze.

4. Las transacciones rechazadas de Transurbano no cuentan como abordajes exitosos.

5. Las llaves originales de los usuarios no se exponen en Gold. Solo se utiliza `usuario_sk`.

6. La identidad entre Transmetro, Transurbano y MetroRiel se aproxima mediante el componente numérico de sus llaves. Aerómetro permanece separado porque su hash no puede relacionarse de manera confiable.

7. Los registros inválidos se conservan en cuarentena con su motivo de rechazo.