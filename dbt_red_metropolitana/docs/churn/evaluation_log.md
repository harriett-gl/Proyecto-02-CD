# Registro de evaluación — Proyecto 02, Fase 02

## Evaluación temporal del modelo Ensemble

- Fecha de registro: 2026-10-31
- Modelo: Random Forest
- Versión: churn-pipeline-v1
- Corte de entrenamiento: A (2026-07-01)
- Corte de evaluación: B (2026-07-31)
- Umbral fijado en A: 0.333333
- Reentrenamiento durante la evaluación: No
- Commit de referencia: Pendiente de registrar al finalizar la entrega

## Resultados del corte B

| Métrica | Resultado |
|---|---:|
| Usuarios evaluados | 58,372 |
| PR-AUC | 0.399490 |
| Precisión | 0.432428 |
| Recall | 0.405786 |
| Verdaderos positivos | 2,707 |
| Falsos positivos | 3,553 |
| Falsos negativos | 3,964 |
| Verdaderos negativos | 48,148 |
| Usuarios a contactar | 6,260 |
| Ganancia esperada | Q9,305 |

## Consideraciones

El umbral se estableció utilizando el corte A y no se modificó a partir de los resultados del corte B.

El corte B había sido evaluado previamente durante la Fase 01, por lo que no constituye una evaluación completamente ciega.

La ganancia representa una estimación basada en los supuestos económicos establecidos, no un ingreso observado.

## Evidencias

- outputs/churn/ensemble_evaluation_B.csv
- outputs/churn/gain_threshold.png
- outputs/churn/selected_policy_A.csv
- docs/churn/phase2_report.md

## Validación de predicciones del corte C

- Fecha de corte: 2026-08-30.
- Modelo: Random Forest, churn-pipeline-v1.
- Reentrenamiento: No.
- Usuarios procesados: 57,925.
- Identificadores duplicados: 0.
- Probabilidades inválidas: 0.
- Usuarios seleccionados para contacto: 6,385.
- Usuarios con tarjeta recuperable: 27,200.
- Usuarios sin tarjeta recuperable: 30,725.
- Separadores antiguos detectados: 0.

### Diagnóstico de identidad

| Categoría | Usuarios |
|---|---:|
| Sin identidad Transmetro/Transurbano | 12,588 |
| Identidad TM/TU sin coincidencia CDC | 18,137 |
| Coincidencia CDC únicamente posterior al corte | 0 |
| Tarjeta válida al corte | 27,200 |
| **Total** | **57,925** |

El corte C no dispone de etiquetas de abandono, por lo que no
se calcularon métricas de PR-AUC, precisión ni recall.

Los usuarios sin tarjeta conservan su predicción, pero no
deben considerarse automáticamente contactables.

No se inventaron tarjetas ni se utilizaron coincidencias
posteriores al corte.

### Evidencias

- outputs/churn/predictions_C_phase2.csv
- docs/churn/card_identity_audit_C.md

## Trazabilidad de la entrega

El commit definitivo se registrará al completar la entrega.

Comando de reproducción:

    python dbt_red_metropolitana/scripts/predecir.py --datos dbt_red_metropolitana --fecha-corte 2026-08-30
