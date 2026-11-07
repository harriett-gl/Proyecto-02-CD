from pathlib import Path
from datetime import datetime
import argparse
import os
import subprocess

import joblib
import numpy as np
import pandas as pd
import psycopg2

from dotenv import load_dotenv


# Obtener argumentos de ejecución
parser = argparse.ArgumentParser(
    description="Predicción de abandono - Red Metropolitana"
)

parser.add_argument(
    "--datos",
    required=True,
    help="Directorio dbt_red_metropolitana o raíz del repositorio",
)

parser.add_argument(
    "--fecha-corte",
    required=True,
    help="Fecha de corte en formato YYYY-MM-DD",
)

args = parser.parse_args()

try:
    cutoff = datetime.strptime(
        args.fecha_corte, "%Y-%m-%d"
    ).date()
except ValueError as exc:
    raise ValueError(
        "La fecha debe tener formato YYYY-MM-DD."
    ) from exc


# Configurar rutas independientes del argumento --datos
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(args.datos).expanduser().resolve()
DBT_DIR = PROJECT_ROOT / "dbt_red_metropolitana"

if not DBT_DIR.is_dir():
    raise FileNotFoundError(
        f"No se encontró el proyecto dbt: {DBT_DIR}"
    )

OUTPUT_DIR = DBT_DIR / "outputs" / "churn"

# --datos identifica la ubicación de los datos de entrada.
# Las características se consultan desde PostgreSQL.
# El modelo y la política siempre pertenecen al proyecto.

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(DBT_DIR / ".env", override=False)

MODEL_PATH = (
    OUTPUT_DIR / "models" / "churn_pipeline_v1.joblib"
)

POLICY_PATH = OUTPUT_DIR / "selected_policy_A.csv"

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró el modelo: {MODEL_PATH}"
    )

if not POLICY_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró la política: {POLICY_PATH}"
    )


# Cargar modelo y umbral sin reentrenar
artifact = joblib.load(MODEL_PATH)
policy = pd.read_csv(POLICY_PATH).iloc[0]

if artifact.get("training_cut") != "A":
    raise RuntimeError(
        "El modelo debe estar entrenado en el corte A."
    )

if policy["selection_cut"] != "A":
    raise RuntimeError(
        "La política debe estar seleccionada en A."
    )

if policy["model"] != "Random Forest":
    raise RuntimeError(
        "El modelo no coincide con la política."
    )

model = artifact["pipeline"]
features = artifact["features"]
threshold = float(policy["threshold"])


# Obtener credenciales de PostgreSQL
password = (
    os.getenv("CHURN_DB_PASSWORD")
    or os.getenv("POSTGRES_PASSWORD")
)

if not password:
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


# Conectar con PostgreSQL
connection = psycopg2.connect(
    host=os.getenv("CHURN_DB_HOST", "localhost"),
    port=int(os.getenv("CHURN_DB_PORT", "5434")),
    dbname=os.getenv(
        "CHURN_DB_NAME", "red_metropolitana_p2"
    ),
    user=os.getenv("CHURN_DB_USER", "red_admin"),
    password=password,
)

try:
    # Consultar características existentes del corte solicitado
    query = """
        SELECT *
        FROM churn.churn_features
        WHERE cutoff_date = %s
        ORDER BY usuario_sk
    """

    df = pd.read_sql_query(
        query,
        connection,
        params=(cutoff,),
    )

    if df.empty:
        raise RuntimeError(
            f"No hay datos para la fecha {cutoff}."
        )

    # Obtener tarjetas identificadas antes o durante el corte
    cards_query = """
        SELECT
            c.usuario_sk,
            STRING_AGG(
                DISTINCT d.usuario_origen_id,
                ';'
            ) AS tarjetas
        FROM churn.churn_features c
        JOIN silver.dim_usuario_conformado d
          ON c.usuario_sk = d.usuario_sk
        WHERE c.cutoff_date = %s
          AND d.modo IN ('TRANSMETRO', 'TRANSURBANO')
          AND EXISTS (
              SELECT 1
              FROM silver.stg_cdc_padron p
              WHERE p.tarjeta = d.usuario_origen_id
                AND p.fecha_cambio < (%s::date + INTERVAL '1 day')
          )
        GROUP BY c.usuario_sk
    """

    cards_df = pd.read_sql_query(
        cards_query,
        connection,
        params=(cutoff, cutoff),
    )

finally:
    connection.close()


# Comprobar integridad de la población
if df["usuario_sk"].isna().any():
    raise RuntimeError(
        "Existen usuarios sin identificador."
    )

if df["usuario_sk"].duplicated().any():
    raise RuntimeError(
        "Existen usuarios duplicados en el corte."
    )

# Preparar las 14 características del modelo
missing = [
    feature
    for feature in features
    if feature not in df.columns
]

if missing:
    raise RuntimeError(
        f"Faltan características: {missing}"
    )

X = df[features].copy()

for column in features:
    X[column] = pd.to_numeric(
        X[column],
        errors="coerce",
    )

X = X.fillna(0).astype(float)

# Realizar predicciones sin entrenar nuevamente
scores = model.predict_proba(X)[:, 1]

if not np.isfinite(scores).all():
    raise RuntimeError(
        "Se generaron probabilidades inválidas."
    )

contact = (scores >= threshold).astype(int)


# Preparar archivo final
predictions = pd.DataFrame({
    "unidad_id": df["usuario_sk"].values,
    "puntaje": scores,
    "contactar": contact,
})

predictions = predictions.merge(
    cards_df.rename(columns={
        "usuario_sk": "unidad_id",
    }),
    on="unidad_id",
    how="left",
    validate="one_to_one",
)

# Mantener explícitamente los usuarios sin tarjeta
predictions["tarjetas"] = (
    predictions["tarjetas"].fillna("")
)

predictions = predictions[
    ["unidad_id", "tarjetas", "puntaje", "contactar"]
]

predictions = predictions.sort_values(
    "unidad_id"
).reset_index(drop=True)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

output_path = (
    OUTPUT_DIR / "predictions_C_phase2.csv"
    if cutoff.isoformat() == "2026-08-30"
    else OUTPUT_DIR / f"predictions_{cutoff}.csv"
)

temporary_path = output_path.with_suffix(".csv.tmp")

predictions.to_csv(
    temporary_path,
    index=False,
    float_format="%.10f",
)

temporary_path.replace(output_path)


# Mostrar resultados
print("\n=== PREDICCIÓN DE ABANDONO ===")
print(f"Fecha de corte: {cutoff}")
print(f"Modelo: {MODEL_PATH.name}")
print(f"Umbral: {threshold:.6f}")
print(f"Usuarios procesados: {len(predictions):,}")
print(
    "Usuarios con tarjeta: "
    f"{predictions['tarjetas'].ne('').sum():,}"
)
print(
    "Usuarios sin tarjeta: "
    f"{predictions['tarjetas'].eq('').sum():,}"
)
print(
    "Usuarios a contactar: "
    f"{predictions['contactar'].sum():,}"
)

print("\n=== ARCHIVO GENERADO ===")
print(output_path)
print("\nPredicción finalizada sin reentrenamiento.")
