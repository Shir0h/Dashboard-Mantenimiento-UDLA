from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# Obtiene la ruta de la carpeta raíz del proyecto a partir del archivo actual.
# Esto permite construir rutas confiables sin depender de la carpeta desde donde
# se ejecute el script.
def get_project_root() -> Path:
    """Devuelve la carpeta principal del proyecto para construir rutas correctas."""
    return Path(__file__).resolve().parent.parent


# Lee la configuración almacenada en el archivo YAML del proyecto.
# Si no existe el archivo o el contenido no es un diccionario, devuelve un valor vacío.
def cargar_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Lee las opciones del archivo YAML de configuración cuando este existe."""
    # Determina la ruta base del proyecto y la ruta del archivo de configuración.
    root = get_project_root()
    path = Path(config_path) if config_path else root / "config.yaml"

    # Convierte rutas relativas a rutas absolutas respecto a la raíz del proyecto.
    if not path.is_absolute():
        path = (root / path).resolve()

    # Si el archivo no existe, evita fallos y devuelve un diccionario vacío.
    if not path.exists():
        return {}

    # Abre el archivo YAML y carga su contenido usando una librería segura.
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    # Asegura que la configuración leída sea un diccionario antes de devolverla.
    return data if isinstance(data, dict) else {}


# Convierte una ruta relativa en una ruta absoluta basada en la raíz del proyecto.
# También permite devolver un valor por defecto cuando no se proporciona una ruta.
def resolver_ruta(valor: str | Path | None, valor_por_defecto: str | Path | None = None) -> Path:
    """Convierte una ruta relativa en una ruta completa usando la base del proyecto."""
    base = get_project_root()

    # Usa el valor recibido o, si es None, el valor por defecto.
    ruta = Path(valor) if valor is not None else valor_por_defecto

    # Si no se proporciona ninguna ruta, devuelve la raíz del proyecto.
    if ruta is None:
        return base

    # Garantiza que la ruta sea un objeto Path antes de normalizarla.
    if not isinstance(ruta, Path):
        ruta = Path(ruta)

    # Si la ruta es relativa, la resuelve con la carpeta raíz del proyecto.
    if not ruta.is_absolute():
        ruta = (base / ruta).resolve()

    return ruta
