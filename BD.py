from pathlib import Path
import sqlite3
import pandas as pd


# Ruta base del proyecto: carpeta donde está este archivo BD.py
BASE_DIR = Path(__file__).resolve().parent

# Archivo CSV de entrada
CSV_PATH = BASE_DIR / "outputs" / "Data_proyecto.csv"

# Base de datos de salida
DB_PATH = BASE_DIR / "base_de_datos_dashboard.db"

# Nombre de la tabla
TABLE_NAME = "ot_dashboard"


def crear_base_datos():
    print("=" * 60)
    print("CREACIÓN BASE DE DATOS SQLITE")
    print("=" * 60)

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"No se encontró el archivo CSV: {CSV_PATH}")

    # Crear carpeta outputs si no existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Leer CSV
    datos = pd.read_csv(CSV_PATH)

    # Conectar a SQLite
    conexion = sqlite3.connect(DB_PATH)

    # Cargar datos a tabla
    datos.to_sql(TABLE_NAME, conexion, if_exists="replace", index=False)

    # Validar cantidad de registros insertados
    cursor = conexion.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    total_registros = cursor.fetchone()[0]

    conexion.close()

    print(f"Archivo CSV leído:        {CSV_PATH}")
    print(f"Base de datos creada:     {DB_PATH}")
    print(f"Tabla creada:             {TABLE_NAME}")
    print(f"Filas cargadas:           {total_registros}")
    print("=" * 60)


if __name__ == "__main__":
    crear_base_datos()