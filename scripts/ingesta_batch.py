import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import time

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = BASE_DIR / "datos_red"
BRONZE_DIR = Path(
    os.environ.get("BRONZE_DIR", str(BASE_DIR / "lake" / "bronze"))
).resolve()
CONTROL_DIR = BRONZE_DIR / "_control"
MANIFEST_FILE = CONTROL_DIR / "batch_manifest.json"

ARCHIVOS_BATCH = [
    "tm_estaciones.csv",
    "tu_paradas.csv",
    "mr_estaciones.csv",
    "am_estaciones.csv",
    "transurbano_transacciones.csv",
    "metroriel_viajes.jsonl",
]


def calcular_hash(ruta):
    sha256 = hashlib.sha256()

    with open(ruta, "rb") as archivo:
        while bloque := archivo.read(1024 * 1024):
            sha256.update(bloque)

    return sha256.hexdigest()


def cargar_manifiesto():
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, "r", encoding="utf-8") as archivo:
            return json.load(archivo)

    return {}


def guardar_manifiesto(manifiesto):
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)

    with open(MANIFEST_FILE, "w", encoding="utf-8") as archivo:
        json.dump(manifiesto, archivo, indent=4, ensure_ascii=False)


def leer_archivo(ruta):
    if ruta.suffix == ".csv":
        return pd.read_csv(
            ruta,
            dtype=str,
            keep_default_na=False
        )

    registros = []

    with open(ruta, "r", encoding="utf-8") as archivo:
        for numero_linea, linea in enumerate(archivo, start=1):
            registros.append({
                "numero_linea": numero_linea,
                "raw_payload": linea.rstrip("\n")
            })

    return pd.DataFrame(registros)


def ejecutar_ingesta_batch():
    manifiesto = cargar_manifiesto()
    fecha_hora = datetime.now(ZoneInfo("America/Guatemala"))
    ingestion_ts = fecha_hora.isoformat()
    ingestion_date = fecha_hora.date().isoformat()

    total_registros = 0

    print("\nINICIANDO INGESTA BATCH HACIA BRONZE\n")

    for nombre_archivo in ARCHIVOS_BATCH:
        inicio = time.perf_counter()
        ruta_origen = SOURCE_DIR / nombre_archivo

        if not ruta_origen.exists():
            print(f"ERROR: no se encontró {nombre_archivo}")
            continue

        archivo_hash = calcular_hash(ruta_origen)
        carga_anterior = manifiesto.get(nombre_archivo)

        if carga_anterior:
            salida_anterior = (
                Path(carga_anterior["archivo_salida"])
                if Path(carga_anterior["archivo_salida"]).is_absolute()
                else BASE_DIR / carga_anterior["archivo_salida"]
            )

            if (
                carga_anterior["sha256"] == archivo_hash
                and salida_anterior.exists()
            ):
                print(f"OMITIDO: {nombre_archivo} ya fue procesado")
                continue

        dataframe = leer_archivo(ruta_origen)

        dataframe["_source_file"] = nombre_archivo
        dataframe["_source_sha256"] = archivo_hash
        dataframe["_ingestion_ts"] = ingestion_ts
        dataframe["_ingestion_date"] = ingestion_date

        nombre_fuente = ruta_origen.stem
        directorio_salida = (
            BRONZE_DIR
            / "batch"
            / nombre_fuente
            / f"ingestion_date={ingestion_date}"
        )

        directorio_salida.mkdir(parents=True, exist_ok=True)

        archivo_salida = (
            directorio_salida
            / f"{archivo_hash[:16]}.parquet"
        )

        dataframe.to_parquet(
            archivo_salida,
            index=False,
            compression="snappy"
        )

        duracion = round(time.perf_counter() - inicio, 3)
        cantidad = len(dataframe)
        total_registros += cantidad

        manifiesto[nombre_archivo] = {
            "sha256": archivo_hash,
            "registros": cantidad,
            "fecha_ingesta": ingestion_ts,
            "duracion_segundos": duracion,
            "archivo_salida": str(
                archivo_salida.resolve()
            )
        }

        print(
            f"PROCESADO: {nombre_archivo} | "
            f"{cantidad:,} registros | {duracion} segundos"
        )

    guardar_manifiesto(manifiesto)

    print(f"\nTOTAL PROCESADO: {total_registros:,} registros")
    print("INGESTA BATCH FINALIZADA\n")


if __name__ == "__main__":
    ejecutar_ingesta_batch()