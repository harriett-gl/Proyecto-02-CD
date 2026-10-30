from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
import psycopg2

from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

# Configuración del proyecto
RANDOM_STATE = 42
N_FOLDS = 5

FEATURE_COLUMNS = [
    "trips_28d",
    "trips_7d",
    "active_days_28d",
    "days_since_last_trip",
    "transport_modes_count",
    "is_multimodal",
    "transmetro_trips",
    "transurbano_trips",
    "metroriel_trips",
    "aerometro_trips",
    "weekend_trip_ratio",
    "peak_hour_trip_ratio",
    "total_spending_gtq",
    "average_spending_gtq",
]

# Obtener la contraseña del contenedor sin mostrarla
result = subprocess.run(
    [
        "docker",
        "exec",
        "postgres-red-metropolitana-p2",
        "printenv",
        "POSTGRES_PASSWORD",
    ],
    capture_output=True,
    text=True,
    check=True,
)

password = result.stdout.strip()

if not password:
    raise RuntimeError("No se encontró la contraseña de PostgreSQL.")

# Conectar con PostgreSQL
connection = psycopg2.connect(
    host="localhost",
    port=5434,
    dbname="red_metropolitana_p2",
    user="red_admin",
    password=password,
)

try:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM churn.churn_features
            WHERE cut_name = 'A'
              AND churn_label IS NOT NULL
            ORDER BY usuario_sk
        """)

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

    df = pd.DataFrame(rows, columns=columns)

finally:
    connection.close()

# Preparar características y etiqueta
X = df[FEATURE_COLUMNS].copy()

for column in FEATURE_COLUMNS:
    X[column] = pd.to_numeric(
        X[column], errors="coerce"
    )

X = X.fillna(0).astype(float)
y = df["churn_label"].astype(int)

# Preparar validación cruzada estratificada
cv = StratifiedKFold(
    n_splits=N_FOLDS,
    shuffle=True,
    random_state=RANDOM_STATE,
)

print("\n=== PREPARACIÓN DE DATOS — CORTE A ===")
print(f"Usuarios: {len(df):,}")
print(f"Características: {len(FEATURE_COLUMNS)}")
print(f"Usuarios churn: {int(y.sum()):,}")
print(f"Usuarios no churn: {int((y == 0).sum()):,}")
print(f"Tasa de abandono: {y.mean() * 100:.2f}%")
print(f"Particiones de validación: {N_FOLDS}")
print(f"Valores faltantes después de preparar X: {int(X.isna().sum().sum())}")

print("\n=== CARACTERÍSTICAS ===")
for column in FEATURE_COLUMNS:
    print(f"- {column}")

print("\nDatos preparados correctamente.")

from sklearn.base import clone
from sklearn.model_selection import cross_validate
from sklearn.metrics import make_scorer
import matplotlib.pyplot as plt
import joblib

# Crear carpetas para resultados y gráficas
OUTPUT_DIR = Path("outputs/churn")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Definir modelos y valores de regularización
C_VALUES = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]

def build_logistic(penalty, c_value):
    return Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(
            l1_ratio=1.0 if penalty == "l1" else 0.0,
            C=c_value,
            solver="liblinear",
            max_iter=2000,
            random_state=RANDOM_STATE,
        )),
    ])

def evaluate_predictions(y_true, scores):
    return {
        "pr_auc": average_precision_score(y_true, scores),
        "roc_auc": roc_auc_score(y_true, scores),
    }

# Evaluar los dos baselines usando exactamente los mismos folds
baseline_results = {
    "Baseline constante": [],
    "Baseline frecuencia": [],
}

for train_idx, val_idx in cv.split(X, y):
    y_train = y.iloc[train_idx]
    y_val = y.iloc[val_idx]

    # Probabilidad constante calculada solo con el fold de entrenamiento
    constant_scores = np.full(
        len(val_idx),
        y_train.mean(),
    )

    # Regla sin entrenamiento: menos viajes implica mayor riesgo
    frequency_scores = -X.iloc[val_idx]["trips_28d"].to_numpy()

    baseline_results["Baseline constante"].append(
        evaluate_predictions(y_val, constant_scores)
    )

    baseline_results["Baseline frecuencia"].append(
        evaluate_predictions(y_val, frequency_scores)
    )

# Evaluar las regresiones logísticas con validación cruzada
all_results = []
regularization_results = []

for name, fold_scores in baseline_results.items():
    all_results.append({
        "model": name,
        "pr_auc_mean": np.mean([s["pr_auc"] for s in fold_scores]),
        "pr_auc_std": np.std([s["pr_auc"] for s in fold_scores]),
        "roc_auc_mean": np.mean([s["roc_auc"] for s in fold_scores]),
        "roc_auc_std": np.std([s["roc_auc"] for s in fold_scores]),
    })

for penalty in ["l1", "l2"]:
    for c_value in C_VALUES:
        model = build_logistic(penalty, c_value)

        scores = cross_validate(
            model,
            X,
            y,
            cv=cv,
            scoring={
                "pr_auc": "average_precision",
                "roc_auc": "roc_auc",
            },
            n_jobs=-1,
            error_score="raise",
        )

        result = {
            "model": f"Logística {penalty.upper()}",
            "penalty": penalty,
            "C": c_value,
            "pr_auc_mean": scores["test_pr_auc"].mean(),
            "pr_auc_std": scores["test_pr_auc"].std(),
            "roc_auc_mean": scores["test_roc_auc"].mean(),
            "roc_auc_std": scores["test_roc_auc"].std(),
        }

        regularization_results.append(result)

# Seleccionar el mejor C de cada regularización usando solo el corte A
regularization_df = pd.DataFrame(regularization_results)

for penalty in ["l1", "l2"]:
    subset = regularization_df[
        regularization_df["penalty"] == penalty
    ]

    best = subset.sort_values(
        ["pr_auc_mean", "C"],
        ascending=[False, True],
    ).iloc[0]

    all_results.append(best.to_dict())

# Guardar tabla comparativa
results_df = pd.DataFrame(all_results)
results_df = results_df.sort_values(
    "pr_auc_mean",
    ascending=False,
)

results_df.to_csv(
    OUTPUT_DIR / "model_comparison_A.csv",
    index=False,
)

regularization_df.to_csv(
    OUTPUT_DIR / "regularization_cv_A.csv",
    index=False,
)

print("\n=== COMPARACIÓN DE MODELOS — CORTE A ===")
print(
    results_df[
        ["model", "pr_auc_mean", "pr_auc_std", "roc_auc_mean"]
    ].to_string(index=False)
)

# Generar gráfica de PR-AUC frente a C
plt.figure(figsize=(9, 5))

for penalty in ["l1", "l2"]:
    subset = regularization_df[
        regularization_df["penalty"] == penalty
    ].sort_values("C")

    plt.errorbar(
        subset["C"],
        subset["pr_auc_mean"],
        yerr=subset["pr_auc_std"],
        marker="o",
        capsize=3,
        label=f"Logística {penalty.upper()}",
    )

plt.xscale("log")
plt.xlabel("C (inverso de la regularización)")
plt.ylabel("PR-AUC promedio")
plt.title("Validación cruzada de regularización — Corte A")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "regularization_curve_A.png",
    dpi=200,
)
plt.close()

# Entrenar el mejor modelo logístico usando todo el corte A
best_logistic = regularization_df.sort_values(
    ["pr_auc_mean", "C"],
    ascending=[False, True],
).iloc[0]

final_model = build_logistic(
    best_logistic["penalty"],
    float(best_logistic["C"]),
)

final_model.fit(X, y)

# Guardar modelo y características utilizadas
joblib.dump(
    {
        "model": final_model,
        "features": FEATURE_COLUMNS,
        "cut": "A",
        "random_state": RANDOM_STATE,
    },
    OUTPUT_DIR / "logistic_model_A.joblib",
)

# Interpretar coeficientes estandarizados
coefficients = pd.DataFrame({
    "feature": FEATURE_COLUMNS,
    "coefficient": final_model.named_steps[
        "model"
    ].coef_[0],
})

coefficients = coefficients.sort_values(
    "coefficient",
    ascending=False,
)

coefficients.to_csv(
    OUTPUT_DIR / "logistic_coefficients_A.csv",
    index=False,
)

print("\n=== CINCO COEFICIENTES POSITIVOS MÁS IMPORTANTES ===")
print(coefficients.head(5).to_string(index=False))

print("\n=== MODELO SELECCIONADO ===")
print(f"Regularización: {best_logistic['penalty'].upper()}")
print(f"C seleccionado: {best_logistic['C']}")
print(f"PR-AUC CV: {best_logistic['pr_auc_mean']:.4f}")

print("\nArchivos guardados en:", OUTPUT_DIR.resolve())
