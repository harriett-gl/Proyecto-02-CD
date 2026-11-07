from pathlib import Path
from datetime import datetime, timezone
import os
import subprocess

import joblib
import numpy as np
import pandas as pd
import psycopg2

from dotenv import load_dotenv
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_score,
    recall_score,
)

# Configuración
ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
OUTPUT_DIR = ROOT / "outputs" / "churn"
DOCS_DIR = PROJECT_ROOT / "docs" / "churn"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")

DATABASE = "red_metropolitana_p2"

MODEL_PATH = (
    OUTPUT_DIR / "random_forest_candidate_A.joblib"
)

POLICY_PATH = OUTPUT_DIR / "selected_policy_A.csv"

# Cargar modelo y política seleccionados en A
artifact = joblib.load(MODEL_PATH)
policy = pd.read_csv(POLICY_PATH).iloc[0]

if artifact.get("cut") != "A":
    raise RuntimeError(
        "El modelo debe estar entrenado con el corte A."
    )

if policy["model"] != "Random Forest":
    raise RuntimeError(
        "La política seleccionada no corresponde "
        "al modelo Random Forest."
    )

if policy["selection_cut"] != "A":
    raise RuntimeError(
        "El umbral debe seleccionarse exclusivamente en A."
    )

model = artifact["model"]
features = artifact["features"]
threshold = float(policy["threshold"])

# Obtener credenciales
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
        "No se encontró POSTGRES_PASSWORD."
    )

# Consultar exclusivamente el corte B
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
        WHERE cut_name = 'B'
        ORDER BY usuario_sk
    """

    df = pd.read_sql_query(query, connection)

finally:
    connection.close()

if df.empty:
    raise RuntimeError(
        "No se encontraron usuarios del corte B."
    )

if df["churn_label"].isna().any():
    raise RuntimeError(
        "El corte B contiene etiquetas nulas."
    )

# Preparar características sin volver a entrenar
X = df[features].copy()

for column in features:
    X[column] = pd.to_numeric(
        X[column],
        errors="coerce",
    )

X = X.fillna(0).astype(float)
y = df["churn_label"].astype(int)

# Generar probabilidades y decisiones
probabilities = model.predict_proba(X)[:, 1]
predictions = (probabilities > threshold).astype(int)

# Calcular métricas
pr_auc = average_precision_score(
    y,
    probabilities,
)

precision = precision_score(
    y,
    predictions,
    zero_division=0,
)

recall = recall_score(
    y,
    predictions,
    zero_division=0,
)

tn, fp, fn, tp = confusion_matrix(
    y,
    predictions,
    labels=[0, 1],
).ravel()

contactos = int(tp + fp)

cost = float(policy["cost_gtq"])
benefit = float(policy["benefit_gtq"])
effectiveness = float(policy["effectiveness"])

gain = (
    tp * effectiveness * benefit
    - contactos * cost
)

# Registrar resultados
results = pd.DataFrame([{
    "model": "Random Forest",
    "training_cut": "A",
    "evaluation_cut": "B",
    "threshold": threshold,
    "users": len(df),
    "pr_auc": pr_auc,
    "precision": precision,
    "recall": recall,
    "tn": tn,
    "fp": fp,
    "fn": fn,
    "tp": tp,
    "contacts": contactos,
    "expected_gain_gtq": gain,
    "evaluated_at_utc": (
        datetime.now(timezone.utc).isoformat()
    ),
}])

results.to_csv(
    OUTPUT_DIR / "ensemble_evaluation_B.csv",
    index=False,
)

# Guardar predicciones auditables
pd.DataFrame({
    "usuario_sk": df["usuario_sk"],
    "cut_name": df["cut_name"],
    "churn_label": y,
    "churn_probability": probabilities,
    "contactar": predictions,
}).to_csv(
    OUTPUT_DIR / "ensemble_predictions_B.csv",
    index=False,
)

# Registrar evaluación en Markdown
log_path = DOCS_DIR / "evaluation_log.md"

with log_path.open("a", encoding="utf-8") as f:
    f.write("\n## Evaluación temporal - Fase 02\n\n")
    f.write(
        f"- Fecha UTC: "
        f"{results.iloc[0]['evaluated_at_utc']}\n"
    )
    f.write("- Modelo: Random Forest entrenado en A\n")
    f.write("- Base de datos: red_metropolitana_p2\n")
    f.write("- Corte evaluado: B\n")
    f.write(f"- Umbral fijado en A: {threshold:.6f}\n")
    f.write(f"- Usuarios: {len(df):,}\n")
    f.write(f"- PR-AUC: {pr_auc:.6f}\n")
    f.write(f"- Precisión: {precision:.6f}\n")
    f.write(f"- Recall: {recall:.6f}\n")
    f.write(
        f"- Matriz de confusión: "
        f"TN={tn}, FP={fp}, FN={fn}, TP={tp}\n"
    )
    f.write(f"- Contactos: {contactos:,}\n")
    f.write(f"- Ganancia esperada: Q{gain:,.2f}\n")
    f.write(
        "- Antecedente: el corte B ya había sido "
        "evaluado con regresión logística en Fase 01.\n"
    )
    f.write(
        "- Esta ejecución no modifica el modelo "
        "ni el umbral seleccionados en A.\n"
    )
    f.write(
        "- Commit: pendiente de registrar "
        "con git rev-parse HEAD.\n"
    )

print("\n=== EVALUACIÓN TEMPORAL EN B ===")
print(f"Usuarios: {len(df):,}")
print(f"Modelo: Random Forest")
print(f"Umbral: {threshold:.6f}")
print(f"PR-AUC: {pr_auc:.6f}")
print(f"Precisión: {precision:.6f}")
print(f"Recall: {recall:.6f}")

print("\n=== MATRIZ DE CONFUSIÓN ===")
print(f"TN: {tn:,}")
print(f"FP: {fp:,}")
print(f"FN: {fn:,}")
print(f"TP: {tp:,}")

print("\n=== RESULTADO ECONÓMICO ===")
print(f"Usuarios contactados: {contactos:,}")
print(f"Ganancia esperada: Q{gain:,.2f}")

print("\nArchivos generados:")
print("ensemble_evaluation_B.csv")
print("ensemble_predictions_B.csv")
print("docs/churn/evaluation_log.md")