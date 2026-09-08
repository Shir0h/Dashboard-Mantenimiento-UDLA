from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from loguru import logger


def configurar_logging(carpeta_logs: str | Path, prefijo: str) -> Path:
    """Configura Loguru con salida colorida en consola y texto limpio en archivo."""
    # Convierte la carpeta de logs a un objeto Path y se asegura de que exista.
    carpeta_logs = Path(carpeta_logs)
    carpeta_logs.mkdir(parents=True, exist_ok=True)

    # Genera un nombre de archivo único por ejecución usando una marca de tiempo.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_log = carpeta_logs / f"{prefijo}_{timestamp}.log"

    # Reinicia la configuración previa de Loguru para evitar duplicar salidas.
    logger.remove()

    # Agrega un sink de archivo con formato simple y legible para guardar los registros.
    logger.add(
        sink=ruta_log,
        level="INFO",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
        backtrace=True,
        diagnose=False,
    )

    # Agrega un sink de consola con colores para ver el progreso en tiempo real.
    logger.add(
        sink=sys.stdout,
        level="INFO",
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{message}</cyan>",
        backtrace=True,
        diagnose=False,
    )

    # Devuelve la ruta del archivo de log creado para que otras funciones puedan consultarla.
    return ruta_log
