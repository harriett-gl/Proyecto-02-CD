from pathlib import Path
import runpy

# Ejecutar el predictor oficial del Proyecto 02.
SCRIPT = (
    Path(__file__).resolve().parent
    / "dbt_red_metropolitana"
    / "scripts"
    / "predecir.py"
)

if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
