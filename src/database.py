from __future__ import annotations

# Módulo encargado de mover datos entre los archivos CSV procesados y la base
# de datos SQLite que consume el dashboard. Concentra en un solo lugar toda la
# lógica de lectura/escritura en SQLite (antes existía una copia duplicada de
# esta misma lógica en el script BD.py de la raíz, con rutas fijas; se
# eliminó para no mantener dos versiones del mismo proceso).
import sqlite3
from pathlib import Path

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

# Ruta por defecto del CSV procesado que se carga a SQLite.
CSV_PATH_DEFAULT = resolver_ruta("outputs/Data_proyecto.csv", "outputs/Data_proyecto.csv")

# Nombre único de la tabla usada tanto para cargar como para leer los datos.
TABLE_NAME = "ot_dashboard"


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
        df.to_sql(TABLE_NAME, conexion, if_exists="replace", index=False)

    return db_path


def cargar_datos_desde_sqlite(db_path: str | Path | None = None) -> pd.DataFrame:
    """Lee la tabla SQLite con los datos de OT listos para el dashboard."""
    # Usa la ruta por defecto si no se proporciona una específica.
    db_path = Path(db_path) if db_path else DB_PATH

    # Abre la conexión y consulta la tabla principal del dashboard.
    with sqlite3.connect(db_path) as conexion:
        return pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conexion)


def main() -> None:
    """Ejecuta la carga de CSV a SQLite desde la terminal e imprime un resumen."""
    # Interfaz de línea de comandos para poder indicar rutas distintas a las de por defecto.
    import argparse

    parser = argparse.ArgumentParser(description="Carga un CSV procesado a la base SQLite del dashboard.")
    parser.add_argument("--input", default=str(CSV_PATH_DEFAULT), help="Ruta del CSV a cargar.")
    parser.add_argument("--db", default=str(DB_PATH), help="Ruta de la base de datos SQLite de salida.")
    args = parser.parse_args()

    csv_path = Path(args.input)
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo CSV: {csv_path}")

    print("=" * 60)
    print("CREACIÓN BASE DE DATOS SQLITE")
    print("=" * 60)

    db_path = cargar_csv_a_sqlite(csv_path, args.db)

    # Vuelve a conectar solo para validar cuántos registros quedaron cargados.
    with sqlite3.connect(db_path) as conexion:
        total_registros = conexion.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]

    print(f"Archivo CSV leído:        {csv_path}")
    print(f"Base de datos creada:     {db_path}")
    print(f"Tabla creada:             {TABLE_NAME}")
    print(f"Filas cargadas:           {total_registros}")
    print("=" * 60)


if __name__ == "__main__":
    main()
