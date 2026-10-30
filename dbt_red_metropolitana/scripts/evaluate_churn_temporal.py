from pathlib import Path
import os
import subprocess

import joblib
import numpy as np
import pandas as pd
import psycopg2

from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)

from dotenv import load_dotenv


# Configuración del proyecto
ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
OUTPUT_DIR = ROOT / "outputs" / "churn"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")

DATABASE = "red_metropolitana_p2_rebuild_test"

MODEL_PATH = OUTPUT_DIR / "logistic_model_A.joblib"

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró el modelo entrenado: {MODEL_PATH}"
    )


# Recuperar credenciales sin mostrarlas
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
    raise RuntimeError("No se encontró POSTGRES_PASSWORD.")


# Cargar el modelo entrenado exclusivamente con el corte A
artifact = joblib.load(MODEL_PATH)

model = artifact["model"]
features = artifact["features"]

if artifact.get("cut") != "A":
    raise RuntimeError(
        "El modelo debe haber sido entrenado con el corte A."
    )


# Consultar los cortes B y C
connection = psycopg2.connect(
    host="localhost",
    port=5434,
    dbname=DATABASE,
    user="red_admin",
    password=password,
)

try:
    query = """
        SELECT *
        FROM churn.churn_features
        WHERE cut_name IN ('B', 'C')
        ORDER BY cut_name, usuario_sk
    """

    df = pd.read_sql_query(query, connection)

finally:
    connection.close()


# Preparar variables usando las mismas columnas del entrenamiento
def prepare_features(data):
    X = data[features].copy()

    for column in features:
        X[column] = pd.to_numeric(
            X[column],
            errors="coerce",
        )

    return X.fillna(0).astype(float)


# Evaluación temporal con el corte B
df_b = df[df["cut_name"] == "B"].copy()

if df_b.empty:
    raise RuntimeError("No se encontraron usuarios del corte B.")

if df_b["churn_label"].isna().any():
    raise RuntimeError(
        "El corte B contiene etiquetas nulas."
    )

X_b = prepare_features(df_b)
y_b = df_b["churn_label"].astype(int)

scores_b = model.predict_proba(X_b)[:, 1]

baseline_constant = np.full(
    len(y_b),
    7396 / 59796,
)

baseline_frequency = -X_b["trips_28d"].to_numpy()


def evaluate(name, y_true, scores):
    return {
        "model": name,
        "pr_auc": average_precision_score(
            y_true,
            scores,
        ),
        "roc_auc": roc_auc_score(
            y_true,
            scores,
        ),
    }


results = [
    evaluate(
        "Logística L2 entrenada en A",
        y_b,
        scores_b,
    ),
    evaluate(
        "Baseline constante",
        y_b,
        baseline_constant,
    ),
    evaluate(
        "Baseline frecuencia",
        y_b,
        baseline_frequency,
    ),
]

metrics_df = pd.DataFrame(results)

metrics_df.to_csv(
    OUTPUT_DIR / "temporal_evaluation_B.csv",
    index=False,
)


# Métricas de clasificación con umbral 0.5
predictions_b = (scores_b >= 0.5).astype(int)

classification = pd.DataFrame([
    {
        "threshold": 0.5,
        "precision": precision_score(
            y_b,
            predictions_b,
            zero_division=0,
        ),
        "recall": recall_score(
            y_b,
            predictions_b,
            zero_division=0,
        ),
        "f1": f1_score(
            y_b,
            predictions_b,
            zero_division=0,
        ),
        "tn": confusion_matrix(y_b, predictions_b)[0, 0],
        "fp": confusion_matrix(y_b, predictions_b)[0, 1],
        "fn": confusion_matrix(y_b, predictions_b)[1, 0],
        "tp": confusion_matrix(y_b, predictions_b)[1, 1],
    }
])

classification.to_csv(
    OUTPUT_DIR / "classification_metrics_B.csv",
    index=False,
)


# Generar predicciones para el corte C
df_c = df[df["cut_name"] == "C"].copy()

if df_c.empty:
    raise RuntimeError("No se encontraron usuarios del corte C.")

if df_c["churn_label"].notna().any():
    raise RuntimeError(
        "El corte C debería conservar etiquetas nulas."
    )

X_c = prepare_features(df_c)

scores_c = model.predict_proba(X_c)[:, 1]

predictions_c = pd.DataFrame({
    "cut_name": df_c["cut_name"].values,
    "cutoff_date": df_c["cutoff_date"].values,
    "usuario_sk": df_c["usuario_sk"].values,
    "churn_probability": scores_c,
    "predicted_churn_05": (
        scores_c >= 0.5
    ).astype(int),
})

predictions_c = predictions_c.sort_values(
    "churn_probability",
    ascending=False,
)

predictions_c.to_csv(
    OUTPUT_DIR / "churn_predictions_C.csv",
    index=False,
)


# Mostrar resultados
print("\n=== EVALUACIÓN TEMPORAL — CORTE B ===")
print(f"Usuarios evaluados: {len(df_b):,}")
print(f"Usuarios churn: {int(y_b.sum()):,}")
print(f"Tasa de abandono: {y_b.mean() * 100:.2f}%")

print("\nCOMPARACIÓN DE MODELOS:")
print(metrics_df.to_string(index=False))

print("\nMÉTRICAS CON UMBRAL 0.5:")
print(classification.to_string(index=False))

print("\n=== PREDICCIONES — CORTE C ===")
print(f"Usuarios: {len(df_c):,}")
print(
    "Probabilidad promedio:",
    round(float(scores_c.mean()), 4),
)
print(
    "Usuarios con probabilidad >= 0.5:",
    int((scores_c >= 0.5).sum()),
)

print("\nARCHIVOS GENERADOS:")
print("- temporal_evaluation_B.csv")
print("- classification_metrics_B.csv")
print("- churn_predictions_C.csv")

print("\nRESULTADO: PASS")
