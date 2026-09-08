"""Convierte archivos Excel (.xlsx / .xls) de una carpeta en archivos CSV.

Este script solo hace la conversión de formato, sin aplicar ningún filtro.
Para dejar solo las filas "Finalizadas" con fechas válidas y enriquecer
Empresa/Formato/Local, usa `src/pipeline.py` (función `procesar_csv`)
sobre el CSV generado aquí.

Genera un log de ejecución (consola + archivo) con el detalle de cada
archivo procesado, filas convertidas y errores encontrados.
"""

# Módulos de línea de comandos, manejo de rutas y registros.
import argparse
from pathlib import Path

import pandas as pd
from loguru import logger

# Intenta importar la utilidad de logging del paquete del proyecto; si se ejecuta
# de forma directa, usa la importación local para no romper la ejecución.
try:
    from src.logging_utils import configurar_logging
except ModuleNotFoundError:
    from logging_utils import configurar_logging


def configurar_logs(carpeta_logs: str = "logs") -> Path:
    """Inicializa los logs para la conversión con formato bonito en consola y archivo."""
    # Crea y configura el sistema de registro para este script.
    return configurar_logging(carpeta_logs, "convercion")


def convertir_excel_a_csv(carpeta_entrada: str, carpeta_salida: str = None) -> list[Path]:
    """Recorre una carpeta, lee los archivos Excel y guarda una copia en formato CSV."""
    # Convierte las rutas de texto a objetos Path para trabajar con ellas más cómodamente.
    carpeta_entrada = Path(carpeta_entrada)
    carpeta_salida = Path(carpeta_salida) if carpeta_salida else carpeta_entrada

    logger.info("Carpeta de entrada: {}", carpeta_entrada.resolve())
    logger.info("Carpeta de salida: {}", carpeta_salida.resolve())

    # Si la carpeta de entrada no existe, termina de inmediato con un registro de error.
    if not carpeta_entrada.exists():
        logger.error("La carpeta de entrada no existe: {}", carpeta_entrada)
        return []

    # Crea la carpeta de salida aunque no exista, para dejar listo el destino de los CSV.
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    # Busca únicamente archivos Excel con extensiones .xlsx y .xls en la carpeta indicada.
    archivos_excel = list(carpeta_entrada.glob('*.xlsx')) + list(carpeta_entrada.glob('*.xls'))

    # Si no se encuentra ningún archivo compatible, se informa y se termina la ejecución.
    if not archivos_excel:
        logger.warning("No se encontraron archivos Excel en {}", carpeta_entrada)
        return []

    logger.info("Se encontraron {} archivo(s) Excel para convertir", len(archivos_excel))

    rutas_csv = []
    errores = 0

    # Procesa cada archivo Excel de forma independiente y registra el resultado de cada conversión.
    for archivo_excel in archivos_excel:
        # Define la ruta del CSV resultante usando el mismo nombre base del archivo Excel.
        ruta_csv = carpeta_salida / f'{archivo_excel.stem}.csv'
        try:
            logger.info("Procesando: {}", archivo_excel.name)
            # Lee el contenido del Excel y lo convierte directamente a DataFrame.
            df = pd.read_excel(archivo_excel)
            # Guarda el contenido como CSV con codificación UTF-8 y BOM para mejor compatibilidad.
            df.to_csv(ruta_csv, index=False, encoding='utf-8-sig')
            rutas_csv.append(ruta_csv)
            logger.info(
                "Convertido correctamente: {} -> {} ({} filas, {} columnas)",
                archivo_excel.name, ruta_csv.name, len(df), len(df.columns)
            )
        except Exception as e:
            # Registra los errores sin interrumpir el procesamiento del resto de archivos.
            errores += 1
            logger.error("Error al convertir {}: {}", archivo_excel.name, e)

    # Muestra un resumen final del proceso con cuántos archivos fueron convertidos y cuántos fallaron.
    logger.info(
        "Resumen final: {} archivo(s) convertido(s) correctamente, {} error(es)",
        len(rutas_csv), errores
    )

    return rutas_csv


# ---------------------------------------------------------------------------
# Bloque de ejecución principal
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    # Define los argumentos de la línea de comandos para controlar la entrada, salida y logs.
    parser = argparse.ArgumentParser(description='Convierte archivos Excel a CSV.')
    parser.add_argument('--input', default='data/raw', help='Carpeta con los archivos Excel de entrada.')
    parser.add_argument('--output', default='outputs', help='Carpeta donde guardar los CSV. Por defecto, la misma de entrada.')
    parser.add_argument('--logs', default='logs', help='Carpeta donde guardar el archivo de log.')
    args = parser.parse_args()

    # Inicializa el archivo de log y registra su ubicación.
    ruta_log = configurar_logs(args.logs)
    logger.info("Log guardado en: {}", ruta_log.resolve())

    # Ejecuta la conversión usando las rutas indicadas por la CLI.
    convertir_excel_a_csv(args.input, args.output)