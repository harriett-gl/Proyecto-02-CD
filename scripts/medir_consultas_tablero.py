"""Mide el tiempo de las consultas del tablero (métrica de Rendimiento).

Ejecuta contra Gold las mismas preguntas que responde el tablero de Tableau,
cinco veces cada una, y reporta la mediana en milisegundos. También imprime
los resultados clave (cobertura, multimodales, caso MetroRiel) para que las
cifras de la documentación salgan de una medición y no de una suposición.

Uso:  python scripts/medir_consultas_tablero.py
"""
from pathlib import Path
import os
import statistics
import time

import psycopg2
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

CONSULTAS = {
    "Demanda por modo (4 modos)": """
        SELECT modo_nombre, SUM(abordajes) FROM gold.rpt_demanda_red
        GROUP BY 1 ORDER BY 2 DESC""",
    "Demanda por zona": """
        SELECT zona_nombre, SUM(cantidad_abordajes) FROM gold.fct_abordajes
        GROUP BY 1 ORDER BY 2 DESC""",
    "Demanda por hora": """
        SELECT h.hora, SUM(f.cantidad_abordajes)
        FROM gold.fct_abordajes f JOIN gold.dim_hora h ON f.hora_sk = h.hora_sk
        GROUP BY 1 ORDER BY 1""",
    "Usuarios multimodales": """
        SELECT cantidad_modos_identificados, COUNT(*) FROM gold.dim_usuario
        GROUP BY 1 ORDER BY 1""",
    "Viajes por estación MetroRiel": """
        SELECT estacion_entrada, SUM(cantidad_viajes) FROM gold.fct_viajes_metroriel
        GROUP BY 1 ORDER BY 2 DESC""",
    "Cobertura por zona": """
        SELECT zona_nombre, modos_con_servicio, sin_servicio
        FROM gold.rpt_cobertura_zona ORDER BY 1""",
    "Caso MetroRiel (ranking)": """
        SELECT zona_nombre, demanda_sin_metroriel, ranking_demanda_sin_metroriel,
               en_trazado_metroriel
        FROM gold.rpt_cobertura_zona ORDER BY 3""",
}


def main():
    conexion = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "red_metropolitana"),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    cursor = conexion.cursor()

    print("\nTIEMPO DE LAS CONSULTAS DEL TABLERO (mediana de 5 ejecuciones)\n")
    print(f"| {'Consulta':<32} | {'Mediana (ms)':>12} |")
    print(f"|{'-' * 34}|{'-' * 13}:|")
    for nombre, consulta in CONSULTAS.items():
        tiempos = []
        for _ in range(5):
            inicio = time.perf_counter()
            cursor.execute(consulta)
            cursor.fetchall()
            tiempos.append((time.perf_counter() - inicio) * 1000)
        print(f"| {nombre:<32} | {statistics.median(tiempos):>12.1f} |")

    print("\nCOBERTURA")
    cursor.execute("""
        SELECT COUNT(*) FILTER (WHERE NOT sin_servicio),
               COUNT(*) FILTER (WHERE sin_servicio),
               STRING_AGG(zona_nombre, ', ') FILTER (WHERE sin_servicio)
        FROM gold.rpt_cobertura_zona""")
    con, sin, zonas = cursor.fetchone()
    print(f"Zonas con servicio: {con} | sin servicio: {sin} ({zonas})")

    cursor.execute("""
        SELECT COUNT(*) FILTER (WHERE es_multimodal), COUNT(*)
        FROM features.features_usuario_movilidad""")
    multi, total = cursor.fetchone()
    print(f"Usuarios multimodales (viajes observados): {multi:,} de {total:,} "
          f"({100 * multi / total:.1f} %)")

    print("\nCASO METRORIEL - ranking de demanda sin MetroRiel")
    cursor.execute("""
        SELECT ranking_demanda_sin_metroriel, zona_nombre, demanda_sin_metroriel,
               en_trazado_metroriel
        FROM gold.rpt_cobertura_zona ORDER BY 1""")
    for rk, zona, demanda, trazado in cursor.fetchall():
        marca = "  <- trazado MetroRiel" if trazado else ""
        print(f"{rk:>3}. {zona:<24} {demanda:>9,}{marca}")

    cursor.close()
    conexion.close()


if __name__ == "__main__":
    main()
