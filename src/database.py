from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

# Intento importar utilidades del proyecto; si el archivo se ejecuta de forma directa,
# se usa la importación alternativa para que siga funcionando.
try:
    from src.config_utils import get_project_root, resolver_ruta
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    from config_utils import get_project_root, resolver_ruta

# Ruta raíz del proyecto y ruta por defecto de la base de datos SQLite.
ROOT = get_project_root()
DB_PATH = resolver_ruta("base_de_datos_dashboard.db", "base_de_datos_dashboard.db")


def cargar_csv_a_sqlite(csv_path: str | Path, db_path: str | Path | None = None) -> Path:
    """Carga un CSV procesado a una tabla SQLite para consumo del dashboard."""
    # Convierte las rutas a objetos Path para manejarlas de forma consistente.
    csv_path = Path(csv_path)
    db_path = Path(db_path) if db_path else DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Lee el archivo CSV con el encoding adecuado y lo conserva como texto.
    df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str)

    # Crea o reemplaza la tabla SQLite con los datos del DataFrame.
    with sqlite3.connect(db_path) as conexion:
        df.to_sql("ot_dashboard", conexion, if_exists="replace", index=False)

    return db_path


def cargar_datos_desde_sqlite(db_path: str | Path | None = None) -> pd.DataFrame:
    """Lee la tabla SQLite con los datos de OT listos para el dashboard."""
    # Usa la ruta por defecto si no se proporciona una específica.
    db_path = Path(db_path) if db_path else DB_PATH

    # Abre la conexión y consulta la tabla principal del dashboard.
    with sqlite3.connect(db_path) as conexion:
        return pd.read_sql_query("SELECT * FROM ot_dashboard", conexion)
