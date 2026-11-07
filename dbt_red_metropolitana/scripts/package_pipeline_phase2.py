from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_DIR / "outputs" / "churn" / "models"

SOURCE_PATH = MODEL_DIR / "random_forest_v1.joblib"
TARGET_PATH = MODEL_DIR / "churn_pipeline_v1.joblib"


def main():
    # Cargar el modelo entrenado en el corte A
    artifact = joblib.load(SOURCE_PATH)

    if artifact["cut"] != "A":
        raise RuntimeError("El modelo no corresponde al corte A.")

    model = artifact["model"]
    features = list(artifact["features"])

    # Construir datos de referencia para configurar el imputador
    reference = pd.DataFrame(
        np.zeros((2, len(features))),
        columns=features,
    )

    # Ajustar únicamente el imputador, sin entrenar el Random Forest
    imputer = SimpleImputer(
        missing_values=np.nan,
        strategy="constant",
        fill_value=0,
        keep_empty_features=True,
    )
    imputer.fit(reference)

    # Conservar el clasificador original
    pipeline = Pipeline([
        ("imputer", imputer),
        ("classifier", model),
    ])

    # Comprobar equivalencia con datos de prueba
    test_data = pd.DataFrame(
        np.zeros((3, len(features))),
        columns=features,
    )
    test_data.iloc[0, 0] = np.nan

    original_scores = model.predict_proba(
        test_data.fillna(0)
    )[:, 1]

    pipeline_scores = pipeline.predict_proba(
        test_data
    )[:, 1]

    if not np.allclose(
        original_scores,
        pipeline_scores,
        rtol=0,
        atol=1e-12,
    ):
        raise RuntimeError("Las probabilidades no coinciden.")

    packaged = {
        "pipeline": pipeline,
        "features": features,
        "training_cut": "A",
        "version": "churn-pipeline-v1",
        "random_state": artifact["random_state"],
        "preprocessing": "SimpleImputer_constant_zero",
    }

    joblib.dump(packaged, TARGET_PATH)

    # Verificar que pueda cargarse nuevamente
    restored = joblib.load(TARGET_PATH)

    restored_scores = restored["pipeline"].predict_proba(
        test_data
    )[:, 1]

    if not np.allclose(
        pipeline_scores,
        restored_scores,
        rtol=0,
        atol=1e-12,
    ):
        raise RuntimeError("El archivo guardado no reproduce los resultados.")

    print("\n=== PIPELINE VERSIONADO ===")
    print(f"Archivo: {TARGET_PATH}")
    print(f"Versión: {packaged['version']}")
    print(f"Características: {len(features)}")
    print("Modelo reentrenado: NO")
    print("Equivalencia: PASS")
    print("Carga del archivo: PASS")


if __name__ == "__main__":
    main()
