import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import time

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_FILE = BASE_DIR / "datos_red" / "cdc_padron_usuarios.csv"
BRONZE_DIR = Path(
    os.environ.get("BRONZE_DIR", str(BASE_DIR / "lake" / "bronze"))
).resolve()
CONTROL_DIR = BRONZE_DIR / "_control"
MANIFEST_FILE = CONTROL_DIR / "cdc_manifest.json"


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


def ejecutar_ingesta_cdc():
    inicio = time.perf_counter()

    if not SOURCE_FILE.exists():
        print("ERROR: no se encontró cdc_padron_usuarios.csv")
        return

    manifiesto = cargar_manifiesto()
    archivo_hash = calcular_hash(SOURCE_FILE)
    carga_anterior = manifiesto.get(SOURCE_FILE.name)

    if carga_anterior:
        salida_anterior = (
                Path(carga_anterior["archivo_salida"])
                if Path(carga_anterior["archivo_salida"]).is_absolute()
                else BASE_DIR / carga_anterior["archivo_salida"]
            )

        if carga_anterior:
            salida_anterior = (
                Path(carga_anterior["archivo_salida"])
                if Path(carga_anterior["archivo_salida"]).is_absolute()
                else BASE_DIR / carga_anterior["archivo_salida"]
            )

            if _output_matches(
                    carga_anterior,
                    archivo_hash,
                    salida_anterior
            ):
                print("OMITIDO: cdc_padron_usuarios.csv ya fue procesado")
                return

    fecha_hora = datetime.now(ZoneInfo("America/Guatemala"))
    ingestion_ts = fecha_hora.isoformat()
    ingestion_date = fecha_hora.date().isoformat()

    dataframe = pd.read_csv(
        SOURCE_FILE,
        dtype=str,
        keep_default_na=False
    )

    dataframe["_source_file"] = SOURCE_FILE.name
    dataframe["_source_sha256"] = archivo_hash
    dataframe["_ingestion_ts"] = ingestion_ts
    dataframe["_ingestion_date"] = ingestion_date

    directorio_salida = (
        BRONZE_DIR
        / "cdc"
        / "padron_usuarios"
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

    manifiesto[SOURCE_FILE.name] = {
        "sha256": archivo_hash,
        "registros": len(dataframe),
        "fecha_ingesta": ingestion_ts,
        "duracion_segundos": duracion,
        "archivo_salida": str(
            archivo_salida.resolve()
        )
    }

    guardar_manifiesto(manifiesto)

    print("\nINGESTA CDC FINALIZADA")
    print(f"Archivo: {SOURCE_FILE.name}")
    print(f"Registros: {len(dataframe):,}")
    print(f"Duración: {duracion} segundos")
    print(f"Salida: {archivo_salida}\n")


def _output_matches(carga_anterior, archivo_hash, salida_anterior):
    return (
        carga_anterior["sha256"] == archivo_hash
        and salida_anterior.exists()
    )


if __name__ == "__main__":
    ejecutar_ingesta_cdc()