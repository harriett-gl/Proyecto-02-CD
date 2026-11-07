from pathlib import Path
import os
import subprocess
import time

import matplotlib
matplotlib.use("Agg")

import joblib
import numpy as np
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt

from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# Configuración general
ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
OUTPUT_DIR = ROOT / "outputs" / "churn"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")

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


# Recuperar la contraseña de PostgreSQL
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
    raise RuntimeError(
        "No se encontró la contraseña de PostgreSQL."
    )


# Conectar con la base de datos
connection = psycopg2.connect(
    host="localhost",
    port=5434,
    dbname=os.getenv(
        "CHURN_DB_NAME",
        "red_metropolitana_p2",
    ),
    user="red_admin",
    password=password,
)

try:
    query = """
        SELECT *
        FROM churn.churn_features
        WHERE cut_name = 'A'
          AND churn_label IS NOT NULL
        ORDER BY usuario_sk
    """

    df = pd.read_sql_query(query, connection)

finally:
    connection.close()


# Preparar las características y etiquetas
X = df[FEATURE_COLUMNS].copy()

for column in FEATURE_COLUMNS:
    X[column] = pd.to_numeric(
        X[column],
        errors="coerce",
    )

X = X.fillna(0).astype(float)
y = df["churn_label"].astype(int)

if X.empty:
    raise RuntimeError(
        "No se encontraron registros para el corte A."
    )

if X.isna().any().any():
    raise RuntimeError(
        "Las características contienen valores nulos."
    )

print("\n=== DATOS DEL CORTE A ===")
print(f"Usuarios: {len(df):,}")
print(f"Características: {len(FEATURE_COLUMNS)}")
print(f"Abandonos: {int(y.sum()):,}")
print(f"Tasa de abandono: {y.mean():.4%}")


# Reutilizar los folds de la Fase 01
cv = StratifiedKFold(
    n_splits=N_FOLDS,
    shuffle=True,
    random_state=RANDOM_STATE,
)


# Modelos a comparar
models = {
    "Logística L2": Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(
            C=0.001,
            solver="liblinear",
            max_iter=2000,
            random_state=RANDOM_STATE,
        )),
    ]),
    "Random Forest": RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        min_samples_leaf=10,
        max_features="sqrt",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),
}


# Evaluar baselines y modelos con los mismos folds
results = []
importance_results = []
oof_predictions = pd.DataFrame({
    "usuario_sk": df["usuario_sk"],
    "churn_label": y,
})

fold_indices = list(cv.split(X, y))


def add_result(name, train_scores, val_scores):
    results.append({
        "model": name,
        "pr_auc_train_mean": np.mean(train_scores),
        "pr_auc_train_std": np.std(train_scores),
        "pr_auc_val_mean": np.mean(val_scores),
        "pr_auc_val_std": np.std(val_scores),
        "generalization_gap": (
            np.mean(train_scores) - np.mean(val_scores)
        ),
    })


print("\n=== EVALUACIÓN DE BASELINES ===")

baseline_constant_train = []
baseline_constant_val = []
baseline_frequency_train = []
baseline_frequency_val = []

for train_idx, val_idx in fold_indices:
    X_train = X.iloc[train_idx]
    X_val = X.iloc[val_idx]
    y_train = y.iloc[train_idx]
    y_val = y.iloc[val_idx]

    constant_train = np.full(
        len(train_idx), y_train.mean()
    )
    constant_val = np.full(
        len(val_idx), y_train.mean()
    )

    frequency_train = -X_train["trips_28d"].to_numpy()
    frequency_val = -X_val["trips_28d"].to_numpy()

    baseline_constant_train.append(
        average_precision_score(
            y_train, constant_train
        )
    )
    baseline_constant_val.append(
        average_precision_score(
            y_val, constant_val
        )
    )

    baseline_frequency_train.append(
        average_precision_score(
            y_train, frequency_train
        )
    )
    baseline_frequency_val.append(
        average_precision_score(
            y_val, frequency_val
        )
    )

add_result(
    "Baseline constante",
    baseline_constant_train,
    baseline_constant_val,
)

add_result(
    "Baseline frecuencia",
    baseline_frequency_train,
    baseline_frequency_val,
)


# Entrenamiento y validación de modelos
for name, estimator in models.items():
    print(f"\n=== ENTRENANDO {name.upper()} ===")

    train_scores = []
    val_scores = []
    prediction_column = (
        "oof_logistic_l2"
        if name == "Logística L2"
        else "oof_random_forest"
    )

    oof_predictions[prediction_column] = np.nan

    for fold_number, (train_idx, val_idx) in enumerate(
        fold_indices, start=1
    ):
        start = time.perf_counter()

        X_train = X.iloc[train_idx]
        X_val = X.iloc[val_idx]
        y_train = y.iloc[train_idx]
        y_val = y.iloc[val_idx]

        # Entrenar exclusivamente con el fold de entrenamiento
        from sklearn.base import clone
        model = clone(estimator)
        model.fit(X_train, y_train)

        train_prob = model.predict_proba(X_train)[:, 1]
        val_prob = model.predict_proba(X_val)[:, 1]

        train_score = average_precision_score(
            y_train, train_prob
        )
        val_score = average_precision_score(
            y_val, val_prob
        )

        train_scores.append(train_score)
        val_scores.append(val_score)

        oof_predictions.loc[
            oof_predictions.index[val_idx],
            prediction_column,
        ] = val_prob

        # Importancia por permutación sobre validación
        if name == "Random Forest":
            importance = permutation_importance(
                model,
                X_val,
                y_val,
                scoring="average_precision",
                n_repeats=3,
                random_state=RANDOM_STATE,
                n_jobs=1,
            )

            for feature, value in zip(
                FEATURE_COLUMNS,
                importance.importances_mean,
            ):
                importance_results.append({
                    "fold": fold_number,
                    "feature": feature,
                    "importance": value,
                })

        elapsed = time.perf_counter() - start

        print(
            f"Fold {fold_number}: "
            f"Train={train_score:.4f} | "
            f"Validación={val_score:.4f} | "
            f"Tiempo={elapsed:.2f}s"
        )

    add_result(name, train_scores, val_scores)


# Guardar tabla comparativa
results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    "pr_auc_val_mean",
    ascending=False,
)

results_df.to_csv(
    OUTPUT_DIR / "model_comparison_phase2.csv",
    index=False,
)

print("\n=== COMPARACIÓN FINAL ===")
print(results_df.to_string(index=False))


# Guardar predicciones fuera de fold para el apartado 2.2
oof_predictions.to_csv(
    OUTPUT_DIR / "oof_predictions_A.csv",
    index=False,
)


# Importancia promedio por permutación
importance_df = pd.DataFrame(importance_results)

importance_summary = (
    importance_df
    .groupby("feature")["importance"]
    .agg(["mean", "std"])
    .reset_index()
    .sort_values("mean", ascending=False)
)

importance_summary.to_csv(
    OUTPUT_DIR / "permutation_importance_A.csv",
    index=False,
)

top_features = importance_summary.head(10)

plt.figure(figsize=(11, 6))

plt.barh(
    top_features["feature"][::-1],
    top_features["mean"][::-1],
)

plt.xlabel("Disminución media de PR-AUC por permutación")
plt.ylabel("Característica")
plt.title(
    "Random Forest: importancia de variables\n"
    "Validación cruzada - Corte A"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "permutation_importance.png",
    dpi=200,
)

plt.close()


# Guardar el Random Forest entrenado con todo A
final_rf = RandomForestClassifier(
    n_estimators=150,
    max_depth=10,
    min_samples_leaf=10,
    max_features="sqrt",
    random_state=RANDOM_STATE,
    n_jobs=-1,
)

final_rf.fit(X, y)

joblib.dump(
    {
        "model": final_rf,
        "features": FEATURE_COLUMNS,
        "cut": "A",
        "version": "ensemble-candidate-v1",
        "random_state": RANDOM_STATE,
    },
    OUTPUT_DIR / "random_forest_candidate_A.joblib",
)


# Mostrar recomendación basada únicamente en A
best = results_df.iloc[0]

print("\n=== RESULTADO DEL EXPERIMENTO ===")
print(f"Mejor modelo en CV: {best['model']}")
print(f"PR-AUC: {best['pr_auc_val_mean']:.6f}")
print(f"Desviación: {best['pr_auc_val_std']:.6f}")

print("\n=== ARCHIVOS GENERADOS ===")
print("model_comparison_phase2.csv")
print("oof_predictions_A.csv")
print("permutation_importance_A.csv")
print("permutation_importance.png")
print("random_forest_candidate_A.joblib")
print("\nEntrenamiento finalizado.")