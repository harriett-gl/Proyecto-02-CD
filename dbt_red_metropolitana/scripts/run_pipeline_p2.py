from pathlib import Path
import argparse
import csv
import hashlib
import os
import subprocess
import sys
import time

import pyarrow.parquet as pq
from kafka import KafkaConsumer, TopicPartition
from dotenv import load_dotenv


DBT_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = DBT_DIR.parent
DATA_DIR = ROOT_DIR / "datos_red"
BRONZE_DIR = ROOT_DIR / "lake" / "bronze"

EXPECTED = {
    "tm_estaciones.csv": ("batch/tm_estaciones", 104),
    "tu_paradas.csv": ("batch/tu_paradas", 328),
    "mr_estaciones.csv": ("batch/mr_estaciones", 22),
    "am_estaciones.csv": ("batch/am_estaciones", 14),
    "transurbano_transacciones.csv": (
        "batch/transurbano_transacciones", 1635788
    ),
    "metroriel_viajes.jsonl": (
        "batch/metroriel_viajes", 590844
    ),
    "cdc_padron_usuarios.csv": (
        "cdc/padron_usuarios", 77636
    ),
    "transmetro_validaciones.csv": (
        "streaming/transmetro", 713786
    ),
    "aerometro_boardings.csv": (
        "streaming/aerometro", 387053
    ),
}


def count_source(path):
    if path.suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as file:
            return sum(1 for line in file if line.strip())

    with path.open("r", encoding="utf-8", newline="") as file:
        return sum(1 for _ in csv.reader(file)) - 1


def validate_sources():
    print("\n=== VALIDACIÓN DE ARCHIVOS ORIGINALES ===", flush=True)

    for name, (_, expected) in EXPECTED.items():
        path = DATA_DIR / name

        if not path.is_file():
            raise FileNotFoundError(f"Archivo faltante: {path}")

        actual = count_source(path)

        if actual != expected:
            raise ValueError(
                f"{name}: esperados={expected}, encontrados={actual}"
            )

        print(f"PASS | {name} | {actual:,}", flush=True)


def validate_bronze(bronze_dir=None):
    bronze_dir = Path(bronze_dir or BRONZE_DIR).resolve()

    print("\n=== VALIDACIÓN DE BRONZE ===", flush=True)
    print(f"Directorio: {bronze_dir}", flush=True)

    for name, (directory, expected) in EXPECTED.items():
        files = sorted(
            (bronze_dir / directory).rglob("*.parquet")
        )

        actual = sum(
            pq.ParquetFile(path).metadata.num_rows
            for path in files
        )

        if actual != expected:
            raise ValueError(
                f"{name}: esperados={expected}, bronze={actual}"
            )

        print(f"PASS | {name} | {actual:,}", flush=True)


def execute(label, command, cwd, env):
    print(f"\n=== {label} ===", flush=True)
    start = time.perf_counter()

    subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
    )

    duration = time.perf_counter() - start
    print(f"PASS | {label} | {duration:.2f} segundos", flush=True)

    if env.get("PIPELINE_TIMINGS_FILE"):
        report_path = Path(env["PIPELINE_TIMINGS_FILE"])
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with report_path.open("a", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow(["etapa", "duracion_segundos", "estado"])
            writer.writerow([label, round(duration, 2), "PASS"])

    return duration




def get_kafka_end_offset(topic):
    consumer = KafkaConsumer(
        bootstrap_servers="localhost:9094",
        enable_auto_commit=False,
        consumer_timeout_ms=10000,
    )

    try:
        partition = TopicPartition(topic, 0)
        offsets = consumer.end_offsets([partition])
        return offsets[partition]
    finally:
        consumer.close()




def execute_streaming(env, bronze_dir, state_file):
    topics = {
        "transmetro": "transmetro-validaciones",
        "aerometro": "aerometro-boardings",
    }

    bronze_dir = Path(bronze_dir).resolve()
    state_file = Path(state_file).resolve()

    streaming_dir = bronze_dir / "streaming"

    if streaming_dir.exists() and any(streaming_dir.rglob("*.parquet")):
        raise RuntimeError(
            f"Ya existen archivos de streaming: {streaming_dir}"
        )

    if state_file.exists():
        raise RuntimeError(
            f"El estado SQLite ya existe: {state_file}"
        )

    for source, topic in topics.items():
        start_offset = get_kafka_end_offset(topic)

        print(
            f"INICIO KAFKA | {source} | "
            f"offset={start_offset}",
            flush=True,
        )

        execute(
            f"KAFKA PRODUCER - {source.upper()}",
            [
                sys.executable,
                "scripts/stream_producer.py",
                source,
            ],
            ROOT_DIR,
            env,
        )

        execute(
            f"KAFKA CONSUMER - {source.upper()}",
            [
                sys.executable,
                "scripts/stream_consumer.py",
                source,
                "--start-offset",
                str(start_offset),
                "--state-file",
                str(state_file),
                "--output-dir",
                str(bronze_dir),
            ],
            ROOT_DIR,
            env,
        )



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["validate", "rebuild-dbt"],
        default="validate",
    )

    args = parser.parse_args()

    load_dotenv(ROOT_DIR / ".env")

    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str(DBT_DIR)

    start = time.perf_counter()

    validate_sources()

    if args.mode == "validate":
        validate_bronze()

    elif args.mode == "rebuild-dbt":
        database = "red_metropolitana_p2_rebuild_test"

        bronze_dir = ROOT_DIR / "lake" / "bronze_rebuild_test"
        state_file = (
            bronze_dir / "_control" / "streaming_state.sqlite"
        )

        if bronze_dir.exists():
            raise RuntimeError(
                "Ya existe el directorio de reconstrucción: "
                f"{bronze_dir}. No se sobrescribirá."
            )

        env["POSTGRES_DB"] = database
        env["BRONZE_DIR"] = str(bronze_dir)
        env["PIPELINE_TIMINGS_FILE"] = str(
            bronze_dir / "_control" / "pipeline_timings.csv"
        )

        print(
            f"BASE DE DATOS DE PRUEBA: {database}",
            flush=True,
        )
        print(
            f"BRONZE INDEPENDIENTE: {bronze_dir}",
            flush=True,
        )

        execute(
            "INGESTA BATCH",
            [sys.executable, "scripts/ingesta_batch.py"],
            ROOT_DIR,
            env,
        )

        execute(
            "INGESTA CDC",
            [sys.executable, "scripts/ingesta_cdc.py"],
            ROOT_DIR,
            env,
        )

        execute_streaming(
            env,
            bronze_dir,
            state_file,
        )

        validate_bronze(bronze_dir)

        execute(
            "CARGA STAGING",
            [sys.executable, "scripts/cargar_staging.py"],
            ROOT_DIR,
            env,
        )

        execute(
            "TRANSFORMACIONES DBT",
            ["dbt", "run", "--profiles-dir", "."],
            DBT_DIR,
            env,
        )

        execute(
            "PRUEBAS DBT",
            ["dbt", "test", "--profiles-dir", "."],
            DBT_DIR,
            env,
        )

    duration = time.perf_counter() - start

    print("\n=== RESULTADO FINAL ===", flush=True)
    print(f"Modo: {args.mode}", flush=True)
    print(f"Duración total: {duration:.2f} segundos", flush=True)
    print("RESULTADO: PASS", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nRESULTADO: ERROR — {error}", file=sys.stderr)
        sys.exit(1)
