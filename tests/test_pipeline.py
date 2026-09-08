import pandas as pd

from src.pipeline import procesar_dataframe


def test_procesar_dataframe_filtra_y_extrae_campos():
    df = pd.DataFrame(
        [
            {
                "ID de Orden de Trabajo": "OT001",
                "Estado": "Finalizadas",
                "Fecha de Inicio": "2026-01-01 10:00:00",
                "Fecha Final": "2026-01-01 11:00:00",
                "Ubicado en ó es Parte de": "WALMART CHILE S.A. / HIPER / 035 RANCAGUA",
            },
            {
                "ID de Orden de Trabajo": "OT002",
                "Estado": "Abiertas",
                "Fecha de Inicio": "2026-01-02 10:00:00",
                "Fecha Final": "2026-01-02 11:00:00",
                "Ubicado en ó es Parte de": "WALMART CHILE S.A. / HIPER / 035 RANCAGUA",
            },
            {
                "ID de Orden de Trabajo": "OT003",
                "Estado": "Finalizadas",
                "Fecha de Inicio": "fecha inválida",
                "Fecha Final": "2026-01-03 11:00:00",
                "Ubicado en ó es Parte de": "WALMART CHILE S.A. / HIPER / 035 RANCAGUA",
            },
        ]
    )

    resultado = procesar_dataframe(df)

    assert len(resultado) == 1
    assert resultado.iloc[0]["Empresa"] == "WALMART CHILE S.A."
    assert resultado.iloc[0]["Formato"] == "HIPER"
    assert resultado.iloc[0]["Local"] == "035 RANCAGUA"
