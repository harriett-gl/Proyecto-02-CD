import os
import subprocess
import sys

import psycopg2
from dotenv import load_dotenv
from pathlib import Path

# Configuración del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# Obtener contraseña de PostgreSQL
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

connection = psycopg2.connect(
    host=os.getenv("CHURN_DB_HOST", "localhost"),
    port=int(os.getenv("CHURN_DB_PORT", "5434")),
    dbname=os.getenv("CHURN_DB_NAME", "red_metropolitana_p2"),
    user=os.getenv("CHURN_DB_USER", "red_admin"),
    password=password,
)

try:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                cut_name,
                cutoff_date,
                COUNT(*) AS usuarios,
                COUNT(*) FILTER (
                    WHERE churn_label IS NOT NULL
                ) AS etiquetas_presentes,
                COUNT(*) FILTER (
                    WHERE churn_label IS NULL
                ) AS etiquetas_nulas,
                COUNT(*) FILTER (
                    WHERE trips_7d > trips_28d
                       OR trips_28d < 2
                       OR days_since_last_trip < 1
                       OR days_since_last_trip > 28
                ) AS inconsistencias
            FROM churn.churn_features
            GROUP BY cut_name, cutoff_date
            ORDER BY cutoff_date
        """)

        results = cursor.fetchall()

finally:
    connection.close()

print("\n=== AUDITORÍA TEMPORAL FASE 02 ===")

expected = {
    "A": ("2026-07-01", 59796),
    "B": ("2026-07-31", 58372),
    "C": ("2026-08-30", 57925),
}

failed = len(results) != 3

for cut_name, cutoff_date, users, labeled, unlabeled, inconsistencies in results:
    print(f"\nCorte: {cut_name}")
    print(f"Fecha: {cutoff_date}")
    print(f"Usuarios: {users:,}")
    print(f"Etiquetas presentes: {labeled:,}")
    print(f"Etiquetas nulas: {unlabeled:,}")
    print(f"Inconsistencias: {inconsistencies:,}")

    if (str(cutoff_date), users) != expected.get(cut_name):
        failed = True

    if inconsistencies:
        failed = True

    if cut_name == "C" and labeled != 0:
        failed = True

    if cut_name in ("A", "B") and unlabeled != 0:
        failed = True

if failed:
    print("\nRESULTADO: FAIL")
    sys.exit(1)

print("\nRESULTADO: PASS")
