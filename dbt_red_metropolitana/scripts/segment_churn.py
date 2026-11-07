from pathlib import Path
import subprocess
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg2

from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# Configuración del proyecto
ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
OUTPUT_DIR = ROOT / "outputs" / "churn"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")

RANDOM_STATE = 42

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

# Recuperar contraseña de PostgreSQL
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

# Conectar a la base de datos
connection = psycopg2.connect(
    host="localhost",
    port=5434,
    dbname="red_metropolitana_p2",
    user="red_admin",
    password=password,
)

try:
    df = pd.read_sql_query(
        """
        SELECT *
        FROM churn.churn_features
        WHERE cut_name = 'A'
          AND churn_label IS NOT NULL
        ORDER BY usuario_sk
        """,
        connection,
    )
finally:
    connection.close()

if df.empty:
    raise RuntimeError("No hay datos del corte A.")

# Preparar y estandarizar características
X = df[FEATURE_COLUMNS].copy()

for column in FEATURE_COLUMNS:
    X[column] = pd.to_numeric(
        X[column], errors="coerce"
    )

X = X.fillna(0).astype(float)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("\n=== DATOS PARA SEGMENTACIÓN ===")
print(f"Usuarios: {len(X):,}")
print(f"Características: {X.shape[1]}")

# Evaluar distintos números de clusters
k_values = list(range(2, 9))
inertias = []
silhouettes = []

# Muestra fija para controlar el costo del cálculo
rng = np.random.default_rng(RANDOM_STATE)
sample_idx = rng.choice(
    len(X),
    size=min(5000, len(X)),
    replace=False,
)

for k in k_values:
    model = KMeans(
        n_clusters=k,
        random_state=RANDOM_STATE,
        n_init=10,
    )

    labels = model.fit_predict(X_scaled)

    inertia = model.inertia_

    silhouette = silhouette_score(
        X_scaled[sample_idx],
        labels[sample_idx],
    )

    inertias.append(inertia)
    silhouettes.append(silhouette)

    print(
        f"K={k} | "
        f"Inercia={inertia:.2f} | "
        f"Silhouette={silhouette:.4f}"
    )

# Guardar métricas de selección
metrics = pd.DataFrame({
    "k": k_values,
    "inertia": inertias,
    "silhouette": silhouettes,
})

metrics.to_csv(
    OUTPUT_DIR / "kmeans_selection_A.csv",
    index=False,
)

# Gráfica del método del codo
plt.figure(figsize=(9, 5))
plt.plot(k_values, inertias, marker="o")
plt.xlabel("Número de clusters (K)")
plt.ylabel("Inercia")
plt.title("Método del codo - Corte A")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "kmeans_elbow.png",
    dpi=200,
)
plt.close()

# Gráfica de silhouette
plt.figure(figsize=(9, 5))
plt.plot(k_values, silhouettes, marker="o")
plt.xlabel("Número de clusters (K)")
plt.ylabel("Silhouette promedio (muestra)")
plt.title("Selección de K por silhouette - Corte A")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "kmeans_silhouette.png",
    dpi=200,
)
plt.close()

# Selección inicial de K por mayor silhouette
best_k = int(
    metrics.loc[
        metrics["silhouette"].idxmax(), "k"
    ]
)

print("\n=== SELECCIÓN DE CLUSTERS ===")
print(f"K seleccionado: {best_k}")

# Entrenar KMeans definitivo sobre A
kmeans = KMeans(
    n_clusters=best_k,
    random_state=RANDOM_STATE,
    n_init=10,
)

labels = kmeans.fit_predict(X_scaled)

df["segment"] = labels

# Resumen de segmentos
summary = (
    df.groupby("segment")
    .agg(
        users=("usuario_sk", "count"),
        churn_rate=("churn_label", "mean"),
    )
    .reset_index()
)

medians = (
    X.assign(segment=labels)
    .groupby("segment")[FEATURE_COLUMNS]
    .median()
    .reset_index()
)

summary = summary.merge(
    medians,
    on="segment",
)

summary["percentage"] = (
    100 * summary["users"] / len(df)
)

summary.to_csv(
    OUTPUT_DIR / "kmeans_segments_A.csv",
    index=False,
)

print("\n=== RESUMEN DE SEGMENTOS ===")
print(
    summary[
        [
            "segment",
            "users",
            "percentage",
            "churn_rate",
            "trips_28d",
            "days_since_last_trip",
        ]
    ].to_string(index=False)
)

# PCA de dos componentes
pca = PCA(n_components=2)
coordinates = pca.fit_transform(X_scaled)

explained = pca.explained_variance_ratio_

print("\n=== PCA ===")
print(f"Varianza PC1: {explained[0]:.4%}")
print(f"Varianza PC2: {explained[1]:.4%}")
print(f"Varianza acumulada: {explained.sum():.4%}")

# Guardar coordenadas para auditoría
pca_df = pd.DataFrame({
    "usuario_sk": df["usuario_sk"],
    "segment": labels,
    "pc1": coordinates[:, 0],
    "pc2": coordinates[:, 1],
})

pca_df.to_csv(
    OUTPUT_DIR / "pca_coordinates_A.csv",
    index=False,
)

# Visualizar una muestra reproducible
plt.figure(figsize=(10, 7))

scatter = plt.scatter(
    coordinates[sample_idx, 0],
    coordinates[sample_idx, 1],
    c=labels[sample_idx],
    cmap="tab10",
    s=8,
    alpha=0.5,
)

plt.colorbar(
    scatter,
    label="Segmento",
)

plt.xlabel(
    f"PC1 ({explained[0]:.2%} de varianza)"
)
plt.ylabel(
    f"PC2 ({explained[1]:.2%} de varianza)"
)
plt.title(
    "Segmentación KMeans y PCA - Corte A"
)
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "pca_segments.png",
    dpi=200,
)

plt.close()

print("\n=== ARCHIVOS GENERADOS ===")
print("kmeans_selection_A.csv")
print("kmeans_segments_A.csv")
print("pca_coordinates_A.csv")
print("kmeans_elbow.png")
print("kmeans_silhouette.png")
print("pca_segments.png")

print("\nSegmentación finalizada.")