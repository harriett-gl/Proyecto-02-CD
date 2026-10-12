import os
import sys
import time
import uuid
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from prefect import flow, task, get_run_logger


RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
CARPETA_DBT = RAIZ_PROYECTO / "dbt_red_metropolitana"
SCRIPT_STAGING = RAIZ_PROYECTO / "scripts" / "cargar_staging.py"
SCRIPT_BATCH = RAIZ_PROYECTO / "scripts" / "ingesta_batch.py"
SCRIPT_CDC = RAIZ_PROYECTO / "scripts" / "ingesta_cdc.py"
SCRIPT_PRODUCER = RAIZ_PROYECTO / "scripts" / "stream_producer.py"
SCRIPT_CONSUMER = RAIZ_PROYECTO / "scripts" / "stream_consumer.py"
load_dotenv(RAIZ_PROYECTO / ".env")


def ejecutable_dbt():
    # Usa el dbt del mismo entorno virtual que ejecuta el flujo
    # (bin/dbt en Linux/macOS, Scripts/dbt.exe en Windows); si no existe,
    # recurre al que esté en el PATH.
    for nombre in ("dbt", "dbt.exe"):
        candidato = Path(sys.executable).parent / nombre
        if candidato.exists():
            return str(candidato)
    return "dbt"

def conexion_postgresql():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv(
            "POSTGRES_DB",
            "red_metropolitana"
        ),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"]
    )


def contar_esquema(cursor, esquema):
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """,
        (esquema,)
    )

    tablas = [fila[0] for fila in cursor.fetchall()]
    total = 0

    for tabla in tablas:
        consulta = sql.SQL(
            "SELECT COUNT(*) FROM {}.{}"
        ).format(
            sql.Identifier(esquema),
            sql.Identifier(tabla)
        )

        cursor.execute(consulta)
        total += cursor.fetchone()[0]

    return total

@task(retries=2, retry_delay_seconds=10)
def ejecutar_ingestas_bronze():
    logger = get_run_logger()

    comandos = [
        (
            [sys.executable, str(SCRIPT_BATCH)],
            "Ingesta Batch"
        ),
        (
            [sys.executable, str(SCRIPT_CDC)],
            "Ingesta CDC"
        ),
        (
            [sys.executable, str(SCRIPT_PRODUCER), "transmetro"],
            "Productor Kafka Transmetro"
        ),
        (
            [sys.executable, str(SCRIPT_CONSUMER), "transmetro"],
            "Consumidor Kafka Transmetro"
        ),
        (
            [sys.executable, str(SCRIPT_PRODUCER), "aerometro"],
            "Productor Kafka Aerómetro"
        ),
        (
            [sys.executable, str(SCRIPT_CONSUMER), "aerometro"],
            "Consumidor Kafka Aerómetro"
        )
    ]

    for comando, nombre in comandos:
        logger.info(f"Ejecutando: {nombre}")

        resultado = subprocess.run(
            comando,
            cwd=RAIZ_PROYECTO,
            text=True,
            capture_output=True
        )

        if resultado.stdout:
            logger.info(resultado.stdout)

        if resultado.returncode != 0:
            raise RuntimeError(
                f"Falló {nombre}:\n{resultado.stderr}"
            )

@task(retries=2, retry_delay_seconds=10)
def cargar_staging():
    logger = get_run_logger()
    logger.info("Cargando archivos en Staging.")

    resultado = subprocess.run(
        [sys.executable, str(SCRIPT_STAGING)],
        cwd=RAIZ_PROYECTO,
        text=True,
        capture_output=True
    )

    if resultado.stdout:
        logger.info(resultado.stdout)

    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr)

    logger.info("Carga de Staging finalizada.")


@task
def ejecutar_dbt():
    logger = get_run_logger()
    logger.info("Ejecutando dbt build.")

    resultado = subprocess.run(
        [
            ejecutable_dbt(),
            "build",
            "--profiles-dir",
            str(CARPETA_DBT)
        ],
        cwd=CARPETA_DBT,
        text=True,
        capture_output=True
    )

    if resultado.stdout:
        logger.info(resultado.stdout)

    if resultado.returncode != 0:
        raise RuntimeError(
            f"dbt build falló:\n{resultado.stderr}"
        )

    logger.info("dbt build finalizó correctamente.")

@task(retries=2, retry_delay_seconds=5)
def registrar_auditoria(
    corrida_id,
    fecha_inicio,
    duracion_segundos,
    estado="EXITOSA"
):
    logger = get_run_logger()

    with conexion_postgresql() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS audit")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit.ejecuciones_pipeline (
                    corrida_id UUID PRIMARY KEY,
                    fecha_inicio TIMESTAMPTZ NOT NULL,
                    fecha_fin TIMESTAMPTZ NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,
                    duracion_segundos NUMERIC(12, 2) NOT NULL,
                    estado TEXT NOT NULL,
                    registros_staging BIGINT NOT NULL,
                    registros_silver BIGINT NOT NULL,
                    registros_gold BIGINT NOT NULL,
                    registros_cuarentena BIGINT NOT NULL
                )
                """
            )

            staging = contar_esquema(cursor, "staging")
            silver = contar_esquema(cursor, "silver")
            gold = contar_esquema(cursor, "gold")
            cuarentena = contar_esquema(
                cursor,
                "quarantine"
            )

            cursor.execute(
                """
                INSERT INTO audit.ejecuciones_pipeline (
                    corrida_id,
                    fecha_inicio,
                    duracion_segundos,
                    estado,
                    registros_staging,
                    registros_silver,
                    registros_gold,
                    registros_cuarentena
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    corrida_id,
                    fecha_inicio,
                    duracion_segundos,
                    estado,
                    staging,
                    silver,
                    gold,
                    cuarentena
                )
            )

    logger.info(f"Auditoría registrada correctamente ({estado}).")


@task
def vaciar_staging():
    logger = get_run_logger()

    with conexion_postgresql() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'staging'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            )

            tablas = [fila[0] for fila in cursor.fetchall()]

            if tablas:
                objetos = [
                    sql.SQL("{}.{}").format(
                        sql.Identifier("staging"),
                        sql.Identifier(tabla)
                    )
                    for tabla in tablas
                ]

                consulta = sql.SQL(
                    "TRUNCATE TABLE {}"
                ).format(sql.SQL(", ").join(objetos))

                cursor.execute(consulta)

    logger.info(
        "Staging fue vaciado; Bronze permanece conservado."
    )


@flow(name="Pipeline Red Metropolitana")
def pipeline_red_metropolitana():
    logger = get_run_logger()
    inicio_total = time.time()

    # Hora real en UTC (antes se guardaba la hora local marcada como +00,
    # lo que desplazaba fecha_inicio 6 horas en audit.ejecuciones_pipeline).
    fecha_inicio = datetime.now(timezone.utc)
    corrida_id = str(uuid.uuid4())

    logger.info(f"Iniciando corrida {corrida_id}")

    try:
        inicio_etapa = time.time()
        ejecutar_ingestas_bronze()
        duracion_bronze = round(time.time() - inicio_etapa, 2)

        inicio_etapa = time.time()
        cargar_staging()
        duracion_staging = round(time.time() - inicio_etapa, 2)

        inicio_etapa = time.time()
        ejecutar_dbt()
        duracion_dbt = round(time.time() - inicio_etapa, 2)

    except Exception:
        # La bitácora también registra las corridas fallidas.
        registrar_auditoria(
            corrida_id,
            fecha_inicio,
            round(time.time() - inicio_total, 2),
            "FALLIDA"
        )
        raise

    duracion_procesamiento = round(
        time.time() - inicio_total,
        2
    )

    inicio_etapa = time.time()
    registrar_auditoria(
        corrida_id,
        fecha_inicio,
        duracion_procesamiento
    )
    duracion_auditoria = round(
        time.time() - inicio_etapa,
        2
    )

    inicio_etapa = time.time()
    vaciar_staging()
    duracion_limpieza = round(
        time.time() - inicio_etapa,
        2
    )

    duracion_total = round(time.time() - inicio_total, 2)

    logger.info(
        "Duraciones por etapa: "
        f"Bronze={duracion_bronze}s, "
        f"Staging={duracion_staging}s, "
        f"dbt={duracion_dbt}s, "
        f"Auditoría={duracion_auditoria}s, "
        f"Limpieza={duracion_limpieza}s, "
        f"Total={duracion_total}s."
    )

    logger.info("Pipeline terminado correctamente.")


if __name__ == "__main__":
    pipeline_red_metropolitana()