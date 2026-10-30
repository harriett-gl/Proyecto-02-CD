from pathlib import Path
import re
import sys

import psycopg2
from dotenv import load_dotenv
import os

# Cargar configuración del proyecto
load_dotenv(Path.cwd().parent / ".env")
load_dotenv(Path.cwd() / ".env")

# Leer el SQL compilado de dbt para reutilizar exactamente
# las mismas transformaciones de características
compiled_files = list(
    Path("target/compiled").rglob("churn_features.sql")
)

if not compiled_files:
    sys.exit("ERROR: No se encontró el SQL compilado de churn_features.")

sql = compiled_files[0].read_text(encoding="utf-8").strip().rstrip(";")

# Restringir ambas fuentes de viajes a datos anteriores al corte A
replacements = {
    '"red_metropolitana_p2"."gold"."fct_abordajes"': """
        (
            SELECT *
            FROM gold.fct_abordajes
            WHERE fecha_hora_local <
                TIMESTAMP '2026-07-01 00:00:00'
                AT TIME ZONE 'America/Guatemala'
        )
    """,
    '"red_metropolitana_p2"."gold"."fct_viajes_metroriel"': """
        (
            SELECT *
            FROM gold.fct_viajes_metroriel
            WHERE fecha_hora_entrada <
                TIMESTAMP '2026-07-01 00:00:00'
        )
    """,
}

for source, replacement in replacements.items():
    count = sql.count(source)
    if count != 1:
        sys.exit(
            f"ERROR: Se esperaba una referencia a {source}; "
            f"se encontraron {count}."
        )
    sql = sql.replace(source, replacement)

# Comparar el resultado reconstruido contra la tabla original
audit_sql = f"""
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
)
SELECT
    (SELECT COUNT(*) FROM original) AS original_users,
    (SELECT COUNT(*) FROM truncated) AS truncated_users,
    (
        SELECT COUNT(*)
        FROM original o
        FULL OUTER JOIN truncated t
          ON o.cut_name = t.cut_name
         AND o.usuario_sk = t.usuario_sk
        WHERE o.usuario_sk IS NULL
           OR t.usuario_sk IS NULL
           OR (to_jsonb(o) - 'churn_label')
              IS DISTINCT FROM
              (to_jsonb(t) - 'churn_label')
    ) AS users_with_differences;
"""

# Ejecutar la auditoría mediante la conexión existente de PostgreSQL
import subprocess

connection = None

# Recuperar la contraseña desde el contenedor, sin imprimirla
result = subprocess.run(
    [
        "docker", "exec",
        "postgres-red-metropolitana-p2",
        "printenv", "POSTGRES_PASSWORD"
    ],
    capture_output=True,
    text=True,
    check=True
)

password = result.stdout.strip()

if not password:
    sys.exit("ERROR: No se encontró POSTGRES_PASSWORD.")

connection = psycopg2.connect(
    host="localhost",
    port=5434,
    dbname="red_metropolitana_p2",
    user="red_admin",
    password=password,
)

try:
    with connection.cursor() as cursor:
        cursor.execute(audit_sql)
        original, truncated, differences = cursor.fetchone()

    print("\n=== AUDITORÍA DE FUGA TEMPORAL — CORTE A ===")
    print(f"Usuarios originales: {original}")
    print(f"Usuarios con datos recortados: {truncated}")
    print(f"Usuarios con diferencias: {differences}")

    if original == truncated and differences == 0:
        print("RESULTADO: PASS — Sin diferencias en las características.")
    else:
        print("RESULTADO: REVISAR — Se detectaron diferencias.")
finally:
    connection.close()
