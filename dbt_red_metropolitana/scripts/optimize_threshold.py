from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Configuración
ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "outputs" / "churn"

COSTO_CONTACTO = 5.0
BENEFICIO_RETENCION = 60.0
EFECTIVIDAD = 0.25

# Leer predicciones fuera de fold del corte A
path = OUTPUT_DIR / "oof_predictions_A.csv"
df = pd.read_csv(path)

# Leer comparación de modelos del corte A
comparison = pd.read_csv(
    OUTPUT_DIR / "model_comparison_phase2.csv"
)

# Seleccionar el modelo con mayor PR-AUC CV en A
best = comparison.sort_values(
    "pr_auc_val_mean",
    ascending=False,
).iloc[0]

model_name = best["model"]

columns = {
    "Random Forest": "oof_random_forest",
    "Logística L2": "oof_logistic_l2",
}

if model_name not in columns:
    raise ValueError(
        f"No hay predicciones OOF para {model_name}"
    )

score_column = columns[model_name]

# Validar los datos
required = ["churn_label", score_column]

if df[required].isna().any().any():
    raise ValueError("Existen valores nulos.")

if not df[score_column].between(0, 1).all():
    raise ValueError("Probabilidades fuera de rango.")

if not df["churn_label"].isin([0, 1]).all():
    raise ValueError("Etiquetas inválidas.")

# Calcular umbral económico
threshold = COSTO_CONTACTO / (
    EFECTIVIDAD * BENEFICIO_RETENCION
)

print("\n=== MODELO SELECCIONADO EN A ===")
print(model_name)

print("\n=== UMBRAL ECONÓMICO ===")
print(f"Costo: Q{COSTO_CONTACTO:.2f}")
print(f"Beneficio: Q{BENEFICIO_RETENCION:.2f}")
print(f"Efectividad: {EFECTIVIDAD:.0%}")
print(f"Umbral teórico: {threshold:.6f}")

# Evaluar umbrales con predicciones OOF de A
y = df["churn_label"].to_numpy()
probabilities = df[score_column].to_numpy()

thresholds = np.unique(
    np.concatenate([
        np.linspace(0, 1, 201),
        [threshold],
    ])
)

results = []

for t in thresholds:
    contactar = probabilities > t

    tp = int(np.sum(contactar & (y == 1)))
    fp = int(np.sum(contactar & (y == 0)))
    fn = int(np.sum(~contactar & (y == 1)))
    tn = int(np.sum(~contactar & (y == 0)))

    contactos = tp + fp

    # Ganancia estimada con etiquetas observadas
    ganancia = (
        tp * EFECTIVIDAD * BENEFICIO_RETENCION
        - contactos * COSTO_CONTACTO
    )

    precision = tp / contactos if contactos else 0
    recall = tp / (tp + fn) if (tp + fn) else 0

    results.append({
        "threshold": t,
        "contactos": contactos,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "ganancia_gtq": ganancia,
    })

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT_DIR / "threshold_gain_A.csv",
    index=False,
)

# Selección económica teórica, sin ajustar con B
selected = results_df.iloc[
    (results_df["threshold"] - threshold)
    .abs().argmin()
]

# Máximo observado solo como diagnóstico en A
best_observed = results_df.loc[
    results_df["ganancia_gtq"].idxmax()
]

# Crear gráfica
plt.figure(figsize=(10, 6))

plt.plot(
    results_df["threshold"],
    results_df["ganancia_gtq"],
    label="Ganancia estimada en A",
)

plt.axvline(
    threshold,
    color="red",
    linestyle="--",
    label=f"Umbral teórico: {threshold:.4f}",
)

plt.axhline(0, color="gray", linewidth=0.8)

plt.xlabel("Umbral de probabilidad")
plt.ylabel("Ganancia estimada (GTQ)")
plt.title(
    "Ganancia económica por umbral\n"
    "Predicciones fuera de fold - Corte A"
)
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "gain_threshold.png",
    dpi=200,
)

plt.close()

# Guardar configuración para etapas posteriores
pd.DataFrame([{
    "model": model_name,
    "score_column": score_column,
    "threshold": threshold,
    "cost_gtq": COSTO_CONTACTO,
    "benefit_gtq": BENEFICIO_RETENCION,
    "effectiveness": EFECTIVIDAD,
    "selection_cut": "A",
}]).to_csv(
    OUTPUT_DIR / "selected_policy_A.csv",
    index=False,
)

print("\n=== POLÍTICA SELECCIONADA ===")
print(f"Modelo: {model_name}")
print(f"Umbral: {threshold:.6f}")
print(f"Usuarios a contactar: {int(selected['contactos']):,}")
print(f"Verdaderos positivos: {int(selected['tp']):,}")
print(f"Falsos positivos: {int(selected['fp']):,}")
print(f"Falsos negativos: {int(selected['fn']):,}")
print(f"Verdaderos negativos: {int(selected['tn']):,}")
print(f"Precisión: {selected['precision']:.4f}")
print(f"Recall: {selected['recall']:.4f}")
print(f"Ganancia estimada: Q{selected['ganancia_gtq']:,.2f}")

print("\n=== MÁXIMO OBSERVADO EN A ===")
print(
    f"Umbral: {best_observed['threshold']:.6f}"
)
print(
    f"Ganancia: Q{best_observed['ganancia_gtq']:,.2f}"
)
print(
    "Este máximo es diagnóstico; no sustituye "
    "automáticamente al umbral teórico."
)

print("\n=== ARCHIVOS GENERADOS ===")
print("threshold_gain_A.csv")
print("selected_policy_A.csv")
print("gain_threshold.png")

print("\nProceso completado.")