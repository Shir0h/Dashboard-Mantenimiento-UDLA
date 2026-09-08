# Dashboard Ejecutivo de Mantenimiento

Proyecto DPL1046 orientado a construir un pipeline en Python para limpiar, transformar y analizar una base de órdenes de trabajo de mantenimiento.

## Estructura del proyecto

```text
dashboard_mantenimiento/
├── data/
│   └── raw/
│       └── Data_proyecto_integrador.xlsx
├── outputs/
├── logs/
├── src/
│   └── __init__.py
├── tests/
│   └── __init__.py
├── limpiar_columnas_por_color.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Primer objetivo

Limpiar la base original conservando únicamente las columnas marcadas en color verde y anaranjado en el encabezado del archivo Excel.

## Uso

1. Copiar el archivo Excel original en:

```text
data/raw/Data_proyecto_integrador.xlsx
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar limpieza:

```bash
python limpiar_columnas_por_color.py
```

O indicando archivo y hoja:

```bash
python limpiar_columnas_por_color.py --input data/raw/Data_proyecto_integrador.xlsx --sheet Hoja1
```

## Salidas esperadas

Los archivos procesados se generan en `outputs/`.

Los registros de ejecución se generan en `logs/`.
