# Dashboard Ejecutivo de Mantenimiento

Proyecto orientado a construir un pipeline robusto en Python para limpiar, transformar y analizar órdenes de trabajo de mantenimiento y exponerlas en un dashboard interactivo.

## Arquitectura actual

```text
dashboard_mantenimiento/
├── dashboard_app.py              # Aplicación Streamlit principal
├── limpiar_columnas_por_color.py # Script de limpieza inicial desde Excel
├── src/
│   ├── __init__.py
│   ├── config_utils.py
│   ├── database.py              # Carga de CSV a SQLite
│   ├── logging_utils.py
│   ├── pipeline.py              # Lógica de filtrado y enriquecimiento
│   └── ...
├── tests/
│   └── test_pipeline.py         # Prueba de regresión del pipeline
├── outputs/                     # CSV procesados y resultados intermedios
├── logs/                        # Registros de ejecución
├── data/raw/                    # Archivos fuente
├── requirements.txt
└── README.md
```

## Flujo recomendado

1. Ejecutar la limpieza desde Excel si aplica:

```bash
python limpiar_columnas_por_color.py
```

2. Procesar el CSV de OT para filtrar y enriquecer la información:

```bash
python -m src.pipeline --input outputs/Data_proyecto.csv --output outputs/ot_procesadas.csv
```

3. Cargar la salida a SQLite para el dashboard:

```bash
python -c "from src.database import cargar_csv_a_sqlite; cargar_csv_a_sqlite('outputs/ot_procesadas.csv')"
```

4. Levantar el dashboard:

```bash
streamlit run dashboard_app.py
```

## Dependencias

Instalar con:

```bash
pip install -r requirements.txt
```

## Salidas esperadas

- Archivos de procesamiento en outputs/
- Registros de ejecución en logs/
- Base SQLite en base_de_datos_dashboard.db
