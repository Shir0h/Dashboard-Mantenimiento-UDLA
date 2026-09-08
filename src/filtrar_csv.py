"""procesar_walmart_finalizados.py

Une en un solo flujo lo que antes hacían dos scripts separados filtrando por
nombre de columna y extrayendo Empresa, Formato y Local de manera segura.
"""

import argparse #Permite que el programa reciba parámetros desde la línea de comandos.
import logging # para  clasificar los mensajes de consola (info, warning)
import re 
import sys
import unicodedata # caracteres especiales
from datetime import datetime
from pathlib import Path

import pandas as pd

LOG_DIR = Path('logs')

FORMATOS_PRIORIDAD = [
    'CENTRAL MAYORISTA',
    'EXPRESS',
    'HIPER',
    'SBA',
    'ACUENTA',
    'UNIMARC',
    'ALVI',
    'SODIMAC',
    'DHL WALMART',
    'DHL',
    'WATTS',
]

def configurar_logging() -> Path:
    """Configura logs tanto para archivo como para una consola limpia y legible."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"procesar_walmart_finalizados_{timestamp}.log"

    # Formato detallado para el archivo log
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        encoding="utf-8"
    )

    # Formato amigable y limpio para la terminal
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)

    return log_path


# ---------------------------------------------------------------------------
# Paso 1: filtrar Finalizados + fechas válidas + Walmart
# ---------------------------------------------------------------------------

def normalizar_texto(valor: str) -> str:
    if not isinstance(valor, str):
        return ''
    texto = valor.strip().lower()
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto


def filtrar_finalizados_con_fechas(
    df: pd.DataFrame,
    columna_fecha_inicio: str = 'Fecha de Inicio',
    columna_fecha_final: str = 'Fecha Final',
    columna_estado: str = 'Estado',
    valor_estado_finalizado: str = 'finalizado',
    columna_ubicacion: str = 'Ubicado en ó es Parte de',
    texto_ubicacion_filtrar: str = 'walmart',
) -> pd.DataFrame:
    columnas_requeridas = [
        columna_fecha_inicio,
        columna_fecha_final,
        columna_estado,
        columna_ubicacion,
    ]
    columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    if columnas_faltantes:
        raise ValueError(f'Faltan las columnas requeridas: {", ".join(columnas_faltantes)}')

    df = df.copy()
    fecha_inicio = pd.to_datetime(df[columna_fecha_inicio], errors='coerce')
    fecha_final = pd.to_datetime(df[columna_fecha_final], errors='coerce')

    estado_normalizado = df[columna_estado].apply(normalizar_texto)
    raiz_finalizado = normalizar_texto(valor_estado_finalizado).rstrip('osa')
    filtro_estado = estado_normalizado.str.contains(raiz_finalizado, regex=False)

    filtro_fechas = fecha_inicio.notna() & fecha_final.notna() & (fecha_inicio <= fecha_final)

    ubicacion_normalizada = df[columna_ubicacion].astype(str).apply(normalizar_texto)
    filtro_ubicacion = ubicacion_normalizada.str.contains(
        normalizar_texto(texto_ubicacion_filtrar), na=False
    )

    return df[filtro_estado & filtro_fechas & filtro_ubicacion].copy()


# ---------------------------------------------------------------------------
# Paso 2: extraer Empresa / Formato / Local
# ---------------------------------------------------------------------------

def limpiar_texto_ubicacion(valor) -> str:
    if pd.isna(valor):
        return ''
    texto = str(valor).strip().upper()
    texto = texto.replace('\\', '/')
    texto = texto.replace('//', '/')
    texto = re.sub(r'/+', '/', texto)
    texto = texto.strip(' /')
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def extraer_empresa(texto: str) -> tuple[str, str]:
    if not texto:
        return '', ''
    """
    Retorna empresa y texto restante.
    """
    patron_walmart = r'WALMART\s+CHILE\s+S\.?A\.?'
    match = re.search(patron_walmart, texto, flags=re.IGNORECASE)

    if match:
        empresa = 'WALMART CHILE S.A.'
        restante = texto[match.end():].strip(' /')
        restante = re.sub(r'\s+', ' ', restante)
        return empresa, restante

    partes = [p.strip() for p in texto.split('/') if p.strip()]

    if len(partes) >= 2:
        empresa = partes[0]
        restante = ' '.join(partes[1:])
        return empresa, restante

    return '', texto


def extraer_formato_y_local(restante: str) -> tuple[str, str]:
    if not restante:
        return '', ''
    """
    Busca el formato dentro del texto restante y extrae el local.
    """
    # Convierte separadores / en espacios para poder buscar formatos.
    texto = restante.replace('/', ' ')
    texto = re.sub(r'\s+', ' ', texto).strip()

    formato_encontrado = ''
    posicion_fin = -1

    for formato in FORMATOS_PRIORIDAD:
        patron = r'\b' + re.escape(formato) + r'\b'
        match = re.search(patron, texto, flags=re.IGNORECASE)

        if match:
            formato_encontrado = formato
            posicion_fin = match.end()
            break

    if not formato_encontrado:
        return '', texto

    local = texto[posicion_fin:].strip()
    # Si el formato viene repetido al inicio del local:
    # "HIPER HIPER 048 CORDILLERA" -> formato HIPER, local "048 CORDILLERA".
    patron_repetido = r"^" + re.escape(formato_encontrado) + r"\b\s*"
    local = re.sub(patron_repetido, "", local, flags=re.IGNORECASE).strip()

    # Si antes del formato venía una cadena como ACUENTA, se ignora por defecto.
    # Ejemplo: "ACUENTA SBA 557 EL SOL" -> formato SBA, local 557 EL SOL.

    return formato_encontrado, local


def parsear_ubicacion(valor) -> dict:
    texto = limpiar_texto_ubicacion(valor)
    empresa, restante = extraer_empresa(texto)
    formato, local = extraer_formato_y_local(restante)
    return {'Empresa': empresa, 'Formato': formato, 'Local': local}

##ESTA PARTE LA CAMBIE YA QUE POR ALGUNA RAZON EL CSV LO TOMABA CON LOS DATOS CORRIDOS Y TENIA POR EJEMPLO LIDER DE PEDRO DE VALDIVIA EN PUERTO MONTT 
def agregar_empresa_formato_local(
    df: pd.DataFrame,
    columna_ubicacion: str = 'Ubicado en ó es Parte de',
) -> pd.DataFrame:
    if columna_ubicacion not in df.columns:
        raise ValueError(f'No existe la columna "{columna_ubicacion}" para extraer Empresa/Formato/Local')

    df = df.copy()
    datos_extraidos = df[columna_ubicacion].apply(parsear_ubicacion)
    df_extraido = pd.DataFrame(list(datos_extraidos), index=df.index)

    posicion_columna = df.columns.get_loc(columna_ubicacion)
    posicion_insertar = posicion_columna + 1

    df_resultado = pd.concat(
        [
            df.iloc[:, :posicion_insertar],
            df_extraido,
            df.iloc[:, posicion_insertar:],
        ],
        axis=1,
    )

    return df_resultado


# ---------------------------------------------------------------------------
# Salidas
# ---------------------------------------------------------------------------

def procesar_carpeta(
    carpeta_entrada: str,
    carpeta_salida: str = 'outputs',
    columna_fecha_inicio: str = 'Fecha de Inicio',
    columna_fecha_final: str = 'Fecha Final',
    columna_estado: str = 'Estado',
    valor_estado_finalizado: str = 'finalizado',
    columna_ubicacion: str = 'Ubicado en ó es Parte de',
    texto_ubicacion_filtrar: str = 'walmart',
) -> list[Path]:
    carpeta_entrada = Path(carpeta_entrada)
    carpeta_salida = Path(carpeta_salida)
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    archivos_csv = sorted(carpeta_entrada.glob('*.csv'))
    if not archivos_csv:
        logging.warning(f'No se encontraron archivos CSV en la carpeta: {carpeta_entrada}')
        return []

    rutas_generadas = []
    archivos_con_error = 0

    logging.info("=" * 60)
    logging.info(f"Iniciando procesamiento de la carpeta: {carpeta_entrada}")
    logging.info(f"Se encontraron {len(archivos_csv)} archivo(s) para procesar.")
    logging.info("=" * 60)

    for archivo_csv in archivos_csv:
        logging.info(f"→ Procesando archivo: {archivo_csv.name}")

        try:
            df = pd.read_csv(archivo_csv, encoding='utf-8-sig', dtype=str)
            total_filas = len(df)

            df_filtrado = filtrar_finalizados_con_fechas(
                df,
                columna_fecha_inicio=columna_fecha_inicio,
                columna_fecha_final=columna_fecha_final,
                columna_estado=columna_estado,
                valor_estado_finalizado=valor_estado_finalizado,
                columna_ubicacion=columna_ubicacion,
                texto_ubicacion_filtrar=texto_ubicacion_filtrar,
            )
            df_resultado = agregar_empresa_formato_local(
                df_filtrado,
                columna_ubicacion=columna_ubicacion,
            )
        except ValueError as exc:
            archivos_con_error += 1
            logging.error(f"Omitido {archivo_csv.name}: {exc}")
            continue
        except Exception as exc:
            archivos_con_error += 1
            logging.exception(f"Error inesperado en {archivo_csv.name}: {exc}")
            continue

        ruta_salida = carpeta_salida / f'{archivo_csv.stem}_Walmart.csv'
        df_resultado.to_csv(ruta_salida, index=False)
        rutas_generadas.append(ruta_salida)

        logging.info(f"  [OK] Conservadas {len(df_filtrado)} de {total_filas} filas.")
        logging.info(f"  [OK] Archivo generado: {ruta_salida.name}\n")

    logging.info("=" * 60)
    logging.info("RESUMEN DE EJECUCIÓN:")
    logging.info(f"  - Procesados con éxito: {len(rutas_generadas)}")
    logging.info(f"  - Con errores u omitidos: {archivos_con_error}")
    logging.info(f"  - Total archivos CSV evaluados: {len(archivos_csv)}")
    logging.info("=" * 60)

    return rutas_generadas


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Filtra CSV (Finalizado + Walmart) y extrae Empresa/Formato/Local de forma acoplada y segura.'
    )
    parser.add_argument('--input', default='outputs', help='Carpeta con los CSV de entrada.')
    parser.add_argument('--output', default='outputs', help='Carpeta donde guardar los archivos de salida.')
    parser.add_argument('--fecha-inicio-col', default='Fecha de Inicio')
    parser.add_argument('--fecha-final-col', default='Fecha Final')
    parser.add_argument('--estado-col', default='Estado')
    parser.add_argument('--estado-finalizado', default='finalizado')
    parser.add_argument('--ubicacion-col', default='Ubicado en ó es Parte de')
    parser.add_argument('--ubicacion-texto', default='walmart')
    args = parser.parse_args()

    log_path = configurar_logging()

    try:
        rutas = procesar_carpeta(
            carpeta_entrada=args.input,
            carpeta_salida=args.output,
            columna_fecha_inicio=args.fecha_inicio_col,
            columna_fecha_final=args.fecha_final_col,
            columna_estado=args.estado_col,
            valor_estado_finalizado=args.estado_finalizado,
            columna_ubicacion=args.ubicacion_col,
            texto_ubicacion_filtrar=args.ubicacion_texto,
        )
        print(f"\n[ÉXITO] Todo el proceso concluyó correctamente. Revisa los detalles en: {log_path}")
    except Exception as exc:
        print(f"\n[CRÍTICO] Ocurrió un error grave durante la ejecución.")
        print(f"Detalle del error: {exc}")
        print(f"Por favor, revisa el archivo de log para más detalles técnicos: {log_path}")
        raise


if __name__ == '__main__':
    main()