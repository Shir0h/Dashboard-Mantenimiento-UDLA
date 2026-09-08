"""Convierte archivos Excel (.xlsx / .xls) de una carpeta en archivos CSV.

Este script solo hace la conversión de formato, sin aplicar ningún filtro.
Para dejar solo las filas "Finalizadas" con fechas válidas, usa el script
`filtrar_csv.py` sobre el CSV generado aquí.

Genera un log de ejecución (consola + archivo) con el detalle de cada
archivo procesado, filas convertidas y errores encontrados.
"""
import argparse
import logging
from pathlib import Path # trabajo de rutas 
from datetime import datetime

import pandas as pd


def configurar_logging(carpeta_logs: str = "logs") -> Path:
    """Configura el logging para escribir tanto en consola como en archivo.

    Args:
        carpeta_logs: Carpeta donde se guardará el archivo de log.

    Returns:
        La ruta del archivo de log creado.
    """
    carpeta_logs = Path(carpeta_logs)
    carpeta_logs.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_log = carpeta_logs / f"convercion_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(ruta_log, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )
    return ruta_log


def convertir_excel_a_csv(carpeta_entrada: str, carpeta_salida: str = None) -> list[Path]:
    """Convierte todos los archivos Excel de una carpeta en archivos CSV.

    Args:
        carpeta_entrada: Ruta de la carpeta con archivos Excel.
        carpeta_salida: Carpeta donde se guardan los CSV generados. Si no se
            especifica, se usa la misma carpeta de entrada.

    Returns:
        Una lista con las rutas de los CSV generados.
    """
    logger = logging.getLogger(__name__)

    carpeta_entrada = Path(carpeta_entrada)
    carpeta_salida = Path(carpeta_salida) if carpeta_salida else carpeta_entrada

    logger.info("Carpeta de entrada: %s", carpeta_entrada.resolve())
    logger.info("Carpeta de salida: %s", carpeta_salida.resolve())

    if not carpeta_entrada.exists():
        logger.error("La carpeta de entrada no existe: %s", carpeta_entrada)
        return []

    carpeta_salida.mkdir(parents=True, exist_ok=True)

    archivos_excel = list(carpeta_entrada.glob('*.xlsx')) + list(carpeta_entrada.glob('*.xls'))

    if not archivos_excel:
        logger.warning("No se encontraron archivos Excel en %s", carpeta_entrada)
        return []

    logger.info("Se encontraron %d archivo(s) Excel para convertir", len(archivos_excel))

    rutas_csv = []
    errores = 0

    for archivo_excel in archivos_excel:
        ruta_csv = carpeta_salida / f'{archivo_excel.stem}.csv'
        try:
            logger.info("Procesando: %s", archivo_excel.name)
            df = pd.read_excel(archivo_excel)
            df.to_csv(ruta_csv, index=False, encoding='utf-8-sig')
            rutas_csv.append(ruta_csv)
            logger.info(
                "Convertido correctamente: %s -> %s (%d filas, %d columnas)",
                archivo_excel.name, ruta_csv.name, len(df), len(df.columns)
            )
        except Exception as e:
            errores += 1
            logger.error("Error al convertir %s: %s", archivo_excel.name, e)

    logger.info(
        "Resumen final: %d archivo(s) convertido(s) correctamente, %d error(es)",
        len(rutas_csv), errores
    )

    return rutas_csv

# ---------------------------------------------------------------------------
# Salidas
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convierte archivos Excel a CSV.')
    parser.add_argument('--input', default='data/raw', help='Carpeta con los archivos Excel de entrada.') # AQUI HAY QUE PASARLO AL ARCHIVO YAML
    parser.add_argument('--output', default='outputs', help='Carpeta donde guardar los CSV. Por defecto, la misma de entrada.') # POR MIENTRAS LA DEJO EN EL OUTP 
    parser.add_argument('--logs', default='logs', help='Carpeta donde guardar el archivo de log.')
    args = parser.parse_args()

    ruta_log = configurar_logging(args.logs)
    logging.getLogger(__name__).info("Log guardado en: %s", ruta_log.resolve())

    convertir_excel_a_csv(args.input, args.output)