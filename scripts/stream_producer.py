from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse
import csv
import json
import time

from kafka import KafkaProducer


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "datos_red"

FUENTES = {
    "transmetro": {
        "archivo": "transmetro_validaciones.csv",
        "topico": "transmetro-validaciones",
        "campo_id": "validacion_id"
    },
    "aerometro": {
        "archivo": "aerometro_boardings.csv",
        "topico": "aerometro-boardings",
        "campo_id": "boarding_id"
    }
}


def crear_productor():
    return KafkaProducer(
        bootstrap_servers="localhost:9094",
        value_serializer=lambda valor: json.dumps(
            valor,
            ensure_ascii=False
        ).encode("utf-8"),
        key_serializer=lambda llave: llave.encode("utf-8"),
        acks="all",
        retries=5,
        linger_ms=20,
        compression_type="gzip",
        enable_idempotence=True
    )


def publicar_fuente(nombre_fuente):
    configuracion = FUENTES[nombre_fuente]
    ruta_archivo = DATA_DIR / configuracion["archivo"]
    topico = configuracion["topico"]
    campo_id = configuracion["campo_id"]

    if not ruta_archivo.exists():
        print(f"ERROR: no se encontró {ruta_archivo}")
        return

    productor = crear_productor()
    inicio = time.perf_counter()
    cantidad = 0

    print(f"\nPublicando {nombre_fuente} en {topico}...\n")

    with open(ruta_archivo, "r", encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)

        for fila in lector:
            event_id = fila[campo_id]

            evento = {
                "event_id": event_id,
                "source": nombre_fuente,
                "source_file": configuracion["archivo"],
                "published_at": datetime.now(
                    ZoneInfo("America/Guatemala")
                ).isoformat(),
                "payload": fila
            }

            productor.send(
                topico,
                key=event_id,
                value=evento
            )

            cantidad += 1

            if cantidad % 50000 == 0:
                print(f"Eventos publicados: {cantidad:,}")

    productor.send(
        topico,
        key="__END__",
        value={
            "control": "END",
            "source": nombre_fuente,
            "total": cantidad
        }
    )

    productor.flush()
    productor.close()

    duracion = round(time.perf_counter() - inicio, 2)

    print(f"\nPUBLICACIÓN FINALIZADA")
    print(f"Fuente: {nombre_fuente}")
    print(f"Eventos publicados: {cantidad:,}")
    print(f"Duración: {duracion} segundos\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "fuente",
        choices=["transmetro", "aerometro"]
    )

    argumentos = parser.parse_args()
    publicar_fuente(argumentos.fuente)


if __name__ == "__main__":
    main()