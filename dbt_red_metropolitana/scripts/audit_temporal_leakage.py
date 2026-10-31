from pathlib import Path
import json
import os
import subprocess
import sys
import psycopg2
from dotenv import load_dotenv

# Configuración del proyecto
DBT_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = DBT_DIR.parent

# Fecha de corte utilizada para la auditoría
CUTOFF_A = "2026-07-01"

# Cargar variables de entorno
load_dotenv(ROOT_DIR / ".env")

# Compilar el modelo utilizando únicamente
# eventos anteriores al corte A
command = [
    "dbt",
    "compile",
    "--select",
    "churn_features",
    "--profiles-dir",
    str(DBT_DIR),
    "--project-dir",
    str(DBT_DIR),
    "--vars",
    json.dumps({
        "churn_audit_cutoff": CUTOFF_A
    }),
]

print("Compilando modelo con datos recortados...")

subprocess.run(
    command,
    cwd=DBT_DIR,
    check=True
)

# Buscar el SQL compilado por dbt
compiled = (
    DBT_DIR
    / "target"
    / "compiled"
    / "dbt_red_metropolitana"
    / "models"
    / "churn"
    / "churn_features.sql"
)

if not compiled.exists():
    sys.exit("ERROR: No se encontró el SQL compilado.")

sql = compiled.read_text(
    encoding="utf-8"
).strip().rstrip(";")

# Comparar características originales
# contra características con datos recortados
# Excluir la etiqueta porque utiliza datos futuros
audit_query = f"""
WITH recalculated AS (
    {sql}
),
original AS (
    SELECT *
    FROM churn.churn_features
    WHERE cut_name = 'A'
),
truncated AS (
    SELECT *
    FROM recalculated
    WHERE cut_name = 'A'
),
comparison AS (
    SELECT
        o.usuario_sk AS original_id,
        t.usuario_sk AS truncated_id,
        (to_jsonb(o) - 'churn_label') AS original_row,
        (to_jsonb(t) - 'churn_label') AS truncated_row
    FROM original o
    FULL OUTER JOIN truncated t
      ON o.cut_name = t.cut_name
     AND o.usuario_sk = t.usuario_sk
)
SELECT
    (SELECT COUNT(*) FROM original),
    (SELECT COUNT(*) FROM truncated),
    (
        SELECT COUNT(*)
        FROM comparison
        WHERE original_id IS NULL
           OR truncated_id IS NULL
           OR original_row IS DISTINCT FROM truncated_row
    );
"""

# Conexión a PostgreSQL mediante .env
connection = psycopg2.connect(
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    port=int(os.environ.get("POSTGRES_PORT", "5432")),
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"]
)

try:
    with connection.cursor() as cursor:
        cursor.execute(audit_query)
        original, truncated, differences = cursor.fetchone()
finally:
    connection.close()

# Mostrar resultados
print("\n=== AUDITORÍA DE FUGA TEMPORAL ===")
print(f"Fecha de corte: {CUTOFF_A}")
print(f"Filas originales: {original}")
print(f"Filas recortadas: {truncated}")
print(f"Diferencias: {differences}")

if original == truncated and differences == 0:
    print("RESULTADO: PASS")
    print("No se detectó fuga temporal en las features.")
else:
    print("RESULTADO: FAIL")
    sys.exit(1)