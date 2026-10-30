from pathlib import Path
import io
import os
import time

import pyarrow.parquet as pq
import psycopg2
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_DIR = Path(
    os.environ.get("BRONZE_DIR", str(BASE_DIR / "lake" / "bronze"))
).resolve()

FUENTES = {
    "tm_estaciones": (
        BRONZE_DIR / "batch" / "tm_estaciones"
    ),
    "tu_paradas": (
        BRONZE_DIR / "batch" / "tu_paradas"
    ),
    "mr_estaciones": (
        BRONZE_DIR / "batch" / "mr_estaciones"
    ),
    "am_estaciones": (
        BRONZE_DIR / "batch" / "am_estaciones"
    ),
    "transurbano_transacciones": (
        BRONZE_DIR / "batch" / "transurbano_transacciones"
    ),
    "metroriel_viajes_raw": (
        BRONZE_DIR / "batch" / "metroriel_viajes"
    ),
    "cdc_padron_usuarios": (
        BRONZE_DIR / "cdc" / "padron_usuarios"
    ),
    "transmetro_validaciones": (
        BRONZE_DIR / "streaming" / "transmetro"
    ),
    "aerometro_boardings": (
        BRONZE_DIR / "streaming" / "aerometro"
    )
}


def conectar_postgres():
    load_dotenv(BASE_DIR / ".env")

    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )


def entre_comillas(nombre):
    return '"' + nombre.replace('"', '""') + '"'


def crear_tabla(cursor, nombre_tabla, columnas):
    columnas_sql = ", ".join(
        f"{entre_comillas(columna)} TEXT"
        for columna in columnas
    )

    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS staging."
        f"{entre_comillas(nombre_tabla)} "
        f"({columnas_sql})"
    )

    cursor.execute(
        f"TRUNCATE TABLE staging."
        f"{entre_comillas(nombre_tabla)}"
    )


def copiar_dataframe(cursor, nombre_tabla, dataframe):
    buffer = io.StringIO()

    dataframe.to_csv(
        buffer,
        index=False,
        header=False,
        na_rep="\\N"
    )

    buffer.seek(0)

    columnas_sql = ", ".join(
        entre_comillas(columna)
        for columna in dataframe.columns
    )

    consulta_copy = (
        f"COPY staging.{entre_comillas(nombre_tabla)} "
        f"({columnas_sql}) "
        "FROM STDIN WITH "
        "(FORMAT CSV, NULL '\\N', HEADER FALSE)"
    )

    cursor.copy_expert(consulta_copy, buffer)


def cargar_fuente(cursor, nombre_tabla, directorio):
    archivos = sorted(directorio.rglob("*.parquet"))

    if not archivos:
        raise FileNotFoundError(
            f"No hay archivos Parquet para {nombre_tabla}: "
            f"{directorio}"
        )

    primer_parquet = pq.ParquetFile(archivos[0])
    columnas = primer_parquet.schema.names

    crear_tabla(cursor, nombre_tabla, columnas)

    total_registros = 0
    inicio = time.perf_counter()

    for archivo in archivos:
        parquet = pq.ParquetFile(archivo)

        for lote in parquet.iter_batches(batch_size=50000):
            dataframe = lote.to_pandas()
            copiar_dataframe(
                cursor,
                nombre_tabla,
                dataframe
            )
            total_registros += len(dataframe)

    duracion = round(time.perf_counter() - inicio, 2)

    print(
        f"{nombre_tabla}: "
        f"{total_registros:,} registros | "
        f"{duracion} segundos"
    )

    return total_registros


def ejecutar_carga_staging():
    conexion = conectar_postgres()
    cursor = conexion.cursor()
    total_general = 0

    print("\nCARGANDO BRONZE HACIA STAGING\n")

    try:
        cursor.execute(
            "CREATE SCHEMA IF NOT EXISTS staging"
        )

        for nombre_tabla, directorio in FUENTES.items():
            cantidad = cargar_fuente(
                cursor,
                nombre_tabla,
                directorio
            )
            total_general += cantidad

        conexion.commit()

        print(
            f"\nTOTAL EN STAGING: "
            f"{total_general:,} registros"
        )
        print("CARGA STAGING FINALIZADA\n")

    except Exception as error:
        conexion.rollback()
        print(f"\nERROR: {error}")
        raise

    finally:
        cursor.close()
        conexion.close()


if __name__ == "__main__":
    ejecutar_carga_staging()