# Tablero en Tableau — qué pregunta responde cada hoja (sección 2.1)

Archivo: [`docs/evidencias/Proyecto 01 - Fase 02.twb`](evidencias/). Conexión:
PostgreSQL `red_metropolitana`, **solo esquema `gold`**.

| Pregunta del enunciado | Hoja | Fuente Gold | Respuesta medida |
|---|---|---|---|
| Demanda por **modo** | Abordajes por modo | `fct_abordajes` (+ `rpt_demanda_red` para incluir MetroRiel) | Transurbano 786,398 · Transmetro 362,106 · MetroRiel 295,511 · Aerómetro 203,554 |
| Demanda por **zona** | Demanda por zona | `fct_abordajes` + `dim_zona` | Mixco 132,768 y Zona 7 117,431 encabezan (sin MetroRiel) |
| Demanda por **hora** | Demanda por hora | `fct_abordajes` + `dim_hora` | Picos 7:00 (162,014) y 17:00 (137,152); 49.7 % en hora pico |
| **Cobertura**: zonas sin servicio de ningún modo | Cobertura por zona | `rpt_cobertura_zona` | 15 zonas con servicio, **1 sin servicio: Santa Catarina Pinula** (946 residentes activos) |
| **Transbordo**: usuarios en más de un sistema | Usuarios multimodales | `dim_usuario` | **36,829** usuarios en 2 o más modos (26,833 en 2; 9,996 en 3) |
| **Caso MetroRiel**: ¿el trazado atiende donde más se necesita? | Viajes por estación MetroRiel + Caso MetroRiel | `fct_viajes_metroriel`, `rpt_cobertura_zona` | Zonas del trazado en puestos 3, 5, 9, 11 y 15 de 15; Mixco y Zona 7 quedan fuera |

## Rastreo hasta el dato crudo

Cada hoja usa tablas Gold declaradas en la *exposure* `tablero_red_metropolitana`
muestra el camino completo, por ejemplo para "Demanda por hora":

`Demanda por hora` → `gold.fct_abordajes` → `silver.transmetro_validaciones` →
`silver.stg_transmetro` → `staging.transmetro_validaciones` →
`lake/bronze/streaming/transmetro/` → `datos_red/transmetro_validaciones.csv`.

## Actualización del libro de Tableau (Fase 02)

Para que el tablero responda cobertura y el caso MetroRiel con cifras:

1. Ejecutar el flujo (`python orchestration/flow_red_metropolitana.py`) para que
   existan las vistas `gold.rpt_cobertura_zona` y `gold.rpt_demanda_red`.
2. En Tableau: *Datos → Nueva fuente de datos → PostgreSQL* → esquema `gold` →
   arrastrar `rpt_cobertura_zona`.
3. Hoja **Cobertura por zona**: Filas = `zona_nombre`; Columnas = `modos_con_servicio`;
   Color = `sin_servicio`. Santa Catarina Pinula aparece con 0 modos.
4. Hoja nueva **Caso MetroRiel**: Filas = `zona_nombre` ordenado por
   `demanda_sin_metroriel` descendente; Columnas = `SUM(demanda_sin_metroriel)`;
   Color = `en_trazado_metroriel`.
5. (Opcional) Hoja **Abordajes por modo** con `rpt_demanda_red` para mostrar los 4 modos.
6. Agregar las hojas al dashboard *Red Metropolitana* y guardar el `.twb`.
