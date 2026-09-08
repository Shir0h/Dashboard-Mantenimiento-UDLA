from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

try:
    from src.config_utils import get_project_root, resolver_ruta
    from src.logging_utils import configurar_logging
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    from config_utils import get_project_root, resolver_ruta
    from logging_utils import configurar_logging

# Ruta base del proyecto y ubicaciones por defecto para entrada, salida y logs.
ROOT = get_project_root()
DEFAULT_INPUT = resolver_ruta("outputs/Data_proyecto.csv", "outputs/Data_proyecto.csv")
DEFAULT_OUTPUT = resolver_ruta("outputs/Data_proyecto.csv", "outputs/Data_proyecto.csv")
DEFAULT_LOG_DIR = resolver_ruta("logs", "logs")

# Lista de formatos de tienda usados para detectar y extraer el formato y el local.
FORMATOS_PRIORIDAD = [
    "CENTRAL MAYORISTA",
    "EXPRESS",
    "HIPER",
    "SBA",
    "ACUENTA",
    "UNIMARC",
    "ALVI",
    "SODIMAC",
    "DHL WALMART",
    "DHL",
    "WATTS",
]


def configurar_logs(carpeta_logs: str | Path | None = None) -> Path:
    """Inicializa los logs del pipeline de forma consistente."""
    # Usa la carpeta de logs por defecto si no se proporciona una ruta específica.
    carpeta = carpeta_logs or DEFAULT_LOG_DIR
    return configurar_logging(carpeta, "pipeline_ot")


def normalizar_texto(valor: Any) -> str:
    """Normaliza texto para comparar de forma estable."""
    # Si el valor no es texto, se devuelve una cadena vacía para evitar errores.
    if not isinstance(valor, str):
        return ""

    # Convierte a minúsculas, elimina espacios y quita tildes para estandarizar comparaciones.
    texto = valor.strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def limpiar_texto_ubicacion(valor: Any) -> str:
    """Deja la ubicación en un formato uniforme para análisis."""
    # Si el valor es nulo, se devuelve una cadena vacía.
    if pd.isna(valor):
        return ""

    # Se normaliza la cadena a mayúsculas y se unifican separadores de ruta.
    texto = str(valor).strip().upper()
    texto = texto.replace("\\", "/")
    texto = texto.replace("//", "/")
    texto = re.sub(r"/+", "/", texto)
    texto = texto.strip(" /")
    texto = re.sub(r"\s+", " ", texto)
    return texto


def extraer_empresa(texto: str) -> tuple[str, str]:
    """Busca el nombre de la empresa dentro del texto de ubicación."""
    # Si la ubicación está vacía, no hay nada que extraer.
    if not texto:
        return "", ""

    # Detecta el patrón específico de Walmart Chile para identificar la empresa.
    patron_walmart = r"WALMART\s+CHILE\s+S\.?A\.?"
    match = re.search(patron_walmart, texto, flags=re.IGNORECASE)
    if match:
        empresa = "WALMART CHILE S.A."
        restante = texto[match.end() :].strip(" /")
        restante = re.sub(r"\s+", " ", restante)
        return empresa, restante

    # Si no encuentra el patrón especial, separa por barras y toma la primera parte como empresa.
    partes = [p.strip() for p in texto.split("/") if p.strip()]
    if len(partes) >= 2:
        empresa = partes[0]
        restante = " ".join(partes[1:])
        return empresa, restante

    return "", texto


def extraer_formato_y_local(restante: str) -> tuple[str, str]:
    """Extrae formato y local del texto restante."""
    # Si no queda texto después de separar la empresa, no hay formato ni local que extraer.
    if not restante:
        return "", ""

    # Normaliza el texto para que la búsqueda de formatos sea más robusta.
    texto = restante.replace("/", " ")
    texto = re.sub(r"\s+", " ", texto).strip()

    formato_encontrado = ""
    posicion_fin = -1

    # Recorre los formatos en orden de prioridad para identificar el primero que aparezca.
    for formato in FORMATOS_PRIORIDAD:
        patron = r"\b" + re.escape(formato) + r"\b"
        match = re.search(patron, texto, flags=re.IGNORECASE)
        if match:
            formato_encontrado = formato
            posicion_fin = match.end()
            break

    # Si no se encuentra un formato conocido, se devuelve el texto completo como local.
    if not formato_encontrado:
        return "", texto

    # Extrae el texto que sigue al formato como el nombre del local.
    local = texto[posicion_fin:].strip()
    patron_repetido = r"^" + re.escape(formato_encontrado) + r"\b\s*"
    local = re.sub(patron_repetido, "", local, flags=re.IGNORECASE).strip()
    return formato_encontrado, local


def parsear_ubicacion(valor: Any) -> dict[str, str]:
    """Transforma una ubicación en Empresa, Formato y Local."""
    # Se limpian los datos de ubicación y luego se extraen los campos estructurados.
    texto = limpiar_texto_ubicacion(valor)
    empresa, restante = extraer_empresa(texto)
    formato, local = extraer_formato_y_local(restante)
    return {"Empresa": empresa, "Formato": formato, "Local": local}


def filtrar_finalizados_con_fechas(
    df: pd.DataFrame,
    columna_fecha_inicio: str = "Fecha de Inicio",
    columna_fecha_final: str = "Fecha Final",
    columna_estado: str = "Estado",
    valor_estado_finalizado: str = "finalizado",
    columna_ubicacion: str = "Ubicado en ó es Parte de",
    texto_ubicacion_filtrar: str = "walmart",
) -> pd.DataFrame:
    """Mantiene solo OT finalizadas con fechas válidas y asociadas a Walmart."""
    # Valida que las columnas necesarias existan antes de procesar.
    columnas_requeridas = [columna_fecha_inicio, columna_fecha_final, columna_estado, columna_ubicacion]
    columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    if columnas_faltantes:
        raise ValueError(f"Faltan las columnas requeridas: {', '.join(columnas_faltantes)}")

    df = df.copy()

    # Convierte las fechas textuales a tipo datetime y elimina las inválidas.
    fecha_inicio = pd.to_datetime(df[columna_fecha_inicio], errors="coerce")
    fecha_final = pd.to_datetime(df[columna_fecha_final], errors="coerce")

    # Normaliza el estado para detectar valores como "Finalizado", "FINALIZADO", etc.
    estado_normalizado = df[columna_estado].astype(str).apply(normalizar_texto)
    raiz_finalizado = normalizar_texto(valor_estado_finalizado).rstrip("osa")
    filtro_estado = estado_normalizado.str.contains(raiz_finalizado, regex=False)

    # Mantiene solo filas con fechas completas y coherentes.
    filtro_fechas = fecha_inicio.notna() & fecha_final.notna() & (fecha_inicio <= fecha_final)

    # Filtra por ubicaciones que contengan el texto de Walmart.
    ubicacion_normalizada = df[columna_ubicacion].astype(str).apply(normalizar_texto)
    filtro_ubicacion = ubicacion_normalizada.str.contains(normalizar_texto(texto_ubicacion_filtrar), na=False)

    return df[filtro_estado & filtro_fechas & filtro_ubicacion].copy()


def agregar_empresa_formato_local(
    df: pd.DataFrame,
    columna_ubicacion: str = "Ubicado en ó es Parte de",
) -> pd.DataFrame:
    """Agrega las columnas Empresa, Formato y Local sin perder el contexto original."""
    # Verifica que la columna de ubicación exista antes de intentar procesarla.
    if columna_ubicacion not in df.columns:
        raise ValueError(f'No existe la columna "{columna_ubicacion}" para extraer Empresa/Formato/Local')

    df = df.copy()

    # Aplica la función de parseo a cada fila para generar las nuevas columnas.
    datos_extraidos = df[columna_ubicacion].apply(parsear_ubicacion)
    df_extraido = pd.DataFrame(list(datos_extraidos), index=df.index)

    # Inserta las nuevas columnas justo después de la columna original de ubicación.
    posicion_columna = df.columns.get_loc(columna_ubicacion)
    posicion_insertar = posicion_columna + 1

    return pd.concat([
        df.iloc[:, :posicion_insertar],
        df_extraido,
        df.iloc[:, posicion_insertar:],
    ], axis=1)


def procesar_dataframe(
    df: pd.DataFrame,
    columna_fecha_inicio: str = "Fecha de Inicio",
    columna_fecha_final: str = "Fecha Final",
    columna_estado: str = "Estado",
    valor_estado_finalizado: str = "finalizado",
    columna_ubicacion: str = "Ubicado en ó es Parte de",
    texto_ubicacion_filtrar: str = "walmart",
) -> pd.DataFrame:
    """Aplica el pipeline completo de filtrado y enriquecimiento a un DataFrame."""
    # Primero se filtran las OT que cumplen con los criterios de negocio.
    df_filtrado = filtrar_finalizados_con_fechas(
        df,
        columna_fecha_inicio=columna_fecha_inicio,
        columna_fecha_final=columna_fecha_final,
        columna_estado=columna_estado,
        valor_estado_finalizado=valor_estado_finalizado,
        columna_ubicacion=columna_ubicacion,
        texto_ubicacion_filtrar=texto_ubicacion_filtrar,
    )

    # Si no hay resultados, se devuelve el DataFrame vacío sin intentar enriquecerlo.
    if df_filtrado.empty:
        return df_filtrado

    # Si hay datos, se añaden las columnas de empresa, formato y local.
    return agregar_empresa_formato_local(df_filtrado, columna_ubicacion=columna_ubicacion)


def procesar_csv(
    input_path: str | Path,
    output_path: str | Path | None = None,
    logs_dir: str | Path | None = None,
) -> Path:
    """Procesa un CSV de OT y genera un CSV enriquecido con Empresa/Formato/Local."""
    # Convierte las rutas a Path y crea la carpeta de salida si no existe.
    input_path = Path(input_path)
    output_path = Path(output_path) if output_path else input_path.with_name("Data_proyecto.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Inicializa el sistema de logs y registra el inicio del procesamiento.
    log_path = configurar_logs(logs_dir)
    logger.info("Procesando archivo: {}", input_path)

    # Lee el CSV fuente y aplica el pipeline completo de transformación.
    df = pd.read_csv(input_path, encoding="utf-8-sig", dtype=str)
    df_procesado = procesar_dataframe(df)

    # Guarda el resultado en un nuevo CSV con el contenido enriquecido.
    df_procesado.to_csv(output_path, index=False, encoding="utf-8-sig")

    # Registra estadísticas útiles del procesamiento para diagnóstico.
    logger.info("Archivo generado: {}", output_path)
    logger.info("Filas procesadas: {}", len(df_procesado))
    return output_path


def main() -> None:
    # Define la interfaz por línea de comandos para ejecutar el pipeline de forma flexible.
    parser = argparse.ArgumentParser(description="Procesa OT de mantenimiento y enriquece ubicación")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Ruta del CSV fuente")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Ruta del CSV procesado")
    parser.add_argument("--logs", default=str(DEFAULT_LOG_DIR), help="Carpeta para logs")
    args = parser.parse_args()

    try:
        # Ejecuta el pipeline completo y obtiene la ruta del archivo generado.
        output_path = procesar_csv(args.input, args.output, args.logs)
        logger.success("Pipeline finalizado correctamente. Salida: {}", output_path)
    except Exception as exc:  # pragma: no cover - CLI safety
        # Registra cualquier error inesperado y lo vuelve a levantar para que la CLI lo reporte.
        logger.exception("Error en el pipeline: {}", exc)
        raise


if __name__ == "__main__":
    main()
