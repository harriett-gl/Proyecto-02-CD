"""Genera docs/diccionario_datos.md a partir de los .yml de dbt (sección 3.1).

Una sola fuente de verdad: las descripciones y los metadatos (fuente y
transformación) se escriben en models/gold/*.yml y models/features/*.yml;
este script los convierte en un documento legible.

Uso:  python scripts/generar_diccionario.py
"""
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
MODELOS = BASE_DIR / "dbt_red_metropolitana" / "models"
SALIDA = BASE_DIR / "docs" / "diccionario_datos.md"

ARCHIVOS = [
    ("Capa Gold - dimensiones", MODELOS / "gold" / "dimensions.yml", "gold"),
    ("Capa Gold - tablas de hechos", MODELOS / "gold" / "facts.yml", "gold"),
    ("Capa Gold - vistas para el tablero", MODELOS / "gold" / "reportes.yml", "gold"),
    ("Capa Features (ciencia de datos)", MODELOS / "features" / "features.yml", "features"),
]


def limpiar(texto):
    return " ".join(str(texto or "").split()).replace("|", "\\|")


def main():
    lineas = [
        "# Diccionario de datos",
        "",
        "> Documento generado con `python scripts/generar_diccionario.py` desde los "
        "archivos `.yml` de dbt. No editar a mano: se edita el `.yml` y se vuelve a generar.",
        "",
        "Para cada campo se indica qué significa, de qué fuente sale y qué "
        "transformación se le aplicó. El linaje gráfico está en "
        "[`docs/linaje/linaje_dbt.png`](linaje/linaje_dbt.png).",
        "",
    ]

    for titulo, archivo, esquema in ARCHIVOS:
        contenido = yaml.safe_load(archivo.read_text(encoding="utf-8"))
        lineas += [f"## {titulo}", ""]

        for modelo in contenido.get("models", []):
            meta = modelo.get("meta", {})
            lineas.append(f"### `{esquema}.{modelo['name']}`")
            lineas.append("")
            lineas.append(limpiar(modelo.get("description")))
            if meta.get("dueno"):
                lineas.append("")
                lineas.append(f"**Dueño:** {meta['dueno']}")
            lineas.append("")

            tiene_meta = any(c.get("meta") for c in modelo.get("columns", []))
            if tiene_meta:
                lineas.append("| Campo | Significado | Fuente | Transformación |")
                lineas.append("|---|---|---|---|")
            else:
                lineas.append("| Campo | Significado |")
                lineas.append("|---|---|")

            for columna in modelo.get("columns", []):
                cmeta = columna.get("meta", {})
                fila = f"| `{columna['name']}` | {limpiar(columna.get('description'))}"
                if tiene_meta:
                    fila += (
                        f" | {limpiar(cmeta.get('fuente'))}"
                        f" | {limpiar(cmeta.get('transformacion'))}"
                    )
                lineas.append(fila + " |")
            lineas.append("")

    SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    print(f"Diccionario generado: {SALIDA}")


if __name__ == "__main__":
    main()
