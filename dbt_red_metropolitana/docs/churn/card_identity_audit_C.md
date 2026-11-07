# Auditoría de identidad y tarjetas — Corte C

## Fecha de corte

2026-08-30

## Objetivo

Verificar la cobertura de identificadores de tarjeta para las
57,925 unidades de análisis del corte C, sin utilizar información
posterior a la fecha de corte.

## Resultados

| Categoría | Usuarios |
|---|---:|
| Sin identidad Transmetro/Transurbano | 12,588 |
| Identidad TM/TU sin coincidencia CDC | 18,137 |
| Coincidencia CDC únicamente posterior al corte | 0 |
| Tarjeta válida al corte | 27,200 |
| Total | 57,925 |

## Interpretación

La población completa cuenta con identificadores internos
usuario_sk y puede recibir predicciones.

De los 57,925 usuarios, 27,200 cuentan con tarjetas recuperables
mediante la relación entre silver.dim_usuario_conformado y
silver.stg_cdc_padron, respetando el corte temporal.

Los 30,725 usuarios restantes no tienen una tarjeta recuperable
mediante esta relación:

- 12,588 no poseen identidad asociada a Transmetro o Transurbano.
- 18,137 poseen identidad TM/TU, pero no presentan coincidencia
  en el padrón CDC.

No se identificaron usuarios cuya única coincidencia CDC fuera
posterior al corte.

## Decisión técnica

Se conserva la columna tarjetas vacía cuando no existe una
asociación válida comprobada.

No se generan identificadores artificiales ni se utilizan
registros posteriores al corte.

Las predicciones se conservan para las 57,925 unidades de análisis.

## Limitación operativa

La ausencia de una tarjeta recuperable puede impedir el contacto
directo mediante ese identificador, aunque el usuario tenga una
predicción válida.

La cobertura de tarjetas es del 46.96 % de la población del corte C.

## Evidencia de ejecución

Archivo:
outputs/churn/predictions_C_phase2.csv

Registros: 57,925

Columnas:
unidad_id, tarjetas, puntaje, contactar

Duplicados: 0

Probabilidades fuera de rango: 0

Usuarios seleccionados para contacto: 6,385
