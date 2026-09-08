from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Se asume la existencia del módulo interno para conectar con la base de datos
from src.database import cargar_datos_desde_sqlite

# Configuración de rutas del proyecto
DB_PATH = Path("base_de_datos_dashboard.db")
CSV_FALLBACK = Path("outputs/Data_proyecto.csv")
CSV_BACKUP = Path("outputs/Data_proyecto.csv")

# Columnas reales obligatorias del archivo .csv
REQUIRED_COLUMNS = [
    "ID de Orden de Trabajo",
    "Estado",
    "Tipo de Tarea",
    "Responsable",
    "Tarea -> Duración Estimada",
    "Tiempo de Ejecución",
    "Fecha de creación de la OT",
]

# Mapeo de columnas visibles en la tabla inferior según la consulta activa (Campos numéricos en minutos)
QUERY_COLUMNS = {
    "Vista General de OTs": [
        "ID de Orden de Trabajo",
        "Estado",
        "Tipo de Tarea",
        "Responsable",
    ],
    "Análisis de Tiempos y Eficiencia": [
        "ID de Orden de Trabajo",
        "Responsable",
        "Duración Estimada (min)",
        "Tiempo de Ejecución (min)",
        "Estado",
    ],
    # Sub-consultas de Responsables (Todas usan minutos numéricos)
    "Volumen por Responsable": ["Responsable", "Estado", "ID de Orden de Trabajo"],
    "Eficiencia de Tiempos": ["Responsable", "Duración Estimada (min)", "Tiempo de Ejecución (min)"],
    "Especialidad por Tarea": ["Responsable", "Tipo de Tarea", "Tiempo de Ejecución (min)"],
    "Urgencias por Operario": ["Responsable", "Tipo de Tarea", "Estado"]
}

# Paleta de colores corporativa pero moderna
PALETA_CORPORATIVA = ["#0F4C81", "#1F77B4", "#4B6584", "#20BF6B", "#26DE81", "#A5B1C2"]

# Configuración inicial de la página de Streamlit
st.set_page_config(page_title="Dashboard OT", page_icon="📊", layout="wide")


@st.cache_data(show_spinner=False)
def cargar_datos() -> pd.DataFrame:
    """Carga los datos desde SQLite o archivos CSV de respaldo si la BD no existe.

    Limpia, estandariza e indexa los campos de texto y convierte las cadenas
    de duraciones (formato '0 days 00:00:00') a valores numéricos en minutos.
    """
    if DB_PATH.exists():
        df = cargar_datos_desde_sqlite(DB_PATH)
    elif CSV_FALLBACK.exists():
        df = pd.read_csv(CSV_FALLBACK, encoding="utf-8-sig", dtype=str)
    elif CSV_BACKUP.exists():
        df = pd.read_csv(CSV_BACKUP, encoding="utf-8-sig", dtype=str)
    else:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    if df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    df = df.copy()
    for columna in REQUIRED_COLUMNS:
        if columna not in df.columns:
            df[columna] = pd.NA

    df["Responsable"] = df["Responsable"].fillna("Sin responsable").astype(str)
    df["Estado"] = df["Estado"].fillna("Sin estado").astype(str)
    df["Tipo de Tarea"] = df["Tipo de Tarea"].fillna("Sin tipo").astype(str)
    
    df["Fecha de creación de la OT"] = pd.to_datetime(
        df["Fecha de creación de la OT"], errors="coerce"
    )
    df["Mes de creación"] = df["Fecha de creación de la OT"].dt.to_period("M").astype(str)

    def convertir_duracion_a_minutos(valor: object) -> float:
        """Parsea cadenas con formato de tiempo complejo a minutos numéricos."""
        if pd.isna(valor):
            return float("nan")
        texto = str(valor).strip()
        if not texto:
            return float("nan")
        match = re.match(r"(?:(\d+)\s+days\s+)?(?:(\d+):)?(\d+):(\d+)", texto)
        if not match:
            return float("nan")
        dias = int(match.group(1) or 0)
        horas = int(match.group(2) or 0)
        minutos = int(match.group(3) or 0)
        segundos = int(match.group(4) or 0)
        return dias * 1440 + horas * 60 + minutos + (segundos / 60)

    df["Duración Estimada (min)"] = df["Tarea -> Duración Estimada"].apply(convertir_duracion_a_minutos)
    df["Tiempo de Ejecución (min)"] = df["Tiempo de Ejecución"].apply(convertir_duracion_a_minutos)
    return df


def main() -> None:
    """Función principal que renderiza la arquitectura jerárquica del dashboard."""
    st.title("Dashboard de Mantenimiento - Órdenes de Trabajo")
    st.caption("Consola analítica 360 basada en registros operativos cargados en la base de datos")

    # Estilos CSS personalizados para implementar botones corporativos modernos
    st.markdown(
        """
        <style>
        .stButton > button {
            background-color: #0F4C81;
            color: white;
            border-radius: 8px;
            border: 1px solid #0F4C81;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #1F77B4;
            border-color: #1F77B4;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    df_filtrado = cargar_datos()
    if df_filtrado.empty:
        st.warning("No se encontraron registros en el sistema. Verifique la carga de datos SQLite.")
        return

    # =========================================================================
    # NAVEGACIÓN INDIVIDUAL POR GRÁFICO
    # =========================================================================
    if "grafico_activo" not in st.session_state:
        st.session_state.grafico_activo = "Volumen de Tareas por Tipo Operativo"

    st.subheader("📊 Selecciona el Gráfico de Análisis")
    
    # Opciones de gráficos disponibles (3 gráficos permitidos)
    graficos_disponibles = [
        "Volumen de Tareas por Tipo Operativo",
        "Comparación Temporal Promedio (Minutos)",
        "Tendencia Mensual de Apertura de OTs"
    ]
    
    # Sistema de botones para navegar entre gráficos
    cols_grafico = st.columns(3)
    for idx, grafico_nombre in enumerate(graficos_disponibles):
        with cols_grafico[idx]:
            estilo_btn = f"✓ {grafico_nombre}" if st.session_state.grafico_activo == grafico_nombre else grafico_nombre
            if st.button(estilo_btn, use_container_width=True, key=f"btn_grafico_{idx}"):
                st.session_state.grafico_activo = grafico_nombre
                st.rerun()

    # =========================================================================
    # RENDERIZACIÓN DEL GRÁFICO ACTIVO (PANTALLA COMPLETA)
    # =========================================================================
    st.markdown("---")
    st.subheader(f"📈 {st.session_state.grafico_activo}")

    # Mapeo de gráficos: cada uno genera los datos necesarios para la tabla posterior
    datos_tabla_activa = None
    
    if st.session_state.grafico_activo == "Volumen de Tareas por Tipo Operativo":
        # Gráfico de volumen de tareas por tipo, desagregado por responsable
        fig_tipo_resp = px.histogram(
            df_filtrado,
            x="Tipo de Tarea",
            color="Responsable",
            text_auto=True,
            barmode="stack",
            template="plotly_white",
            color_discrete_sequence=PALETA_CORPORATIVA,
            title="Volumen de Tareas por Tipo Operativo"
        )
        fig_tipo_resp.update_traces(textposition="outside")
        st.plotly_chart(fig_tipo_resp, use_container_width=True)
        
        # Datos específicos para la tabla: agrupar por Tipo de Tarea y Responsable
        datos_tabla_activa = df_filtrado.groupby(["Tipo de Tarea", "Responsable"], as_index=False).size().rename(columns={"size": "Cantidad de OTs"})
        columnas_tabla_dinamica = ["Tipo de Tarea", "Responsable", "Cantidad de OTs"]

    elif st.session_state.grafico_activo == "Comparación Temporal Promedio (Minutos)":
        # Gráfico de comparación de tiempos estimados vs reales por tipo de tarea
        df_tiempos_barras = df_filtrado.groupby("Tipo de Tarea", as_index=False).agg(
            Estimado=("Duración Estimada (min)", "mean"),
            Real=("Tiempo de Ejecución (min)", "mean")
        )
        df_tiempos_melt = df_tiempos_barras.melt(
            id_vars="Tipo de Tarea",
            value_vars=["Estimado", "Real"],
            var_name="Medición de Tiempo",
            value_name="Minutos"
        )
        fig_tiempos_comp = px.bar(
            df_tiempos_melt,
            x="Tipo de Tarea",
            y="Minutos",
            color="Medición de Tiempo",
            barmode="group",
            text_auto=".1f",
            template="plotly_white",
            color_discrete_sequence=["#4B6584", "#1F77B4"],
            title="Comparación Temporal Promedio (Minutos)"
        )
        fig_tiempos_comp.update_traces(textposition="outside")
        st.plotly_chart(fig_tiempos_comp, use_container_width=True)
        
        # Datos específicos para la tabla: detalles de duración por tipo de tarea
        datos_tabla_activa = df_filtrado[["ID de Orden de Trabajo", "Tipo de Tarea", "Duración Estimada (min)", "Tiempo de Ejecución (min)"]].copy()
        datos_tabla_activa["Duración Estimada (min)"] = datos_tabla_activa["Duración Estimada (min)"].round(1)
        datos_tabla_activa["Tiempo de Ejecución (min)"] = datos_tabla_activa["Tiempo de Ejecución (min)"].round(1)
        columnas_tabla_dinamica = ["ID de Orden de Trabajo", "Tipo de Tarea", "Duración Estimada (min)", "Tiempo de Ejecución (min)"]

    else:  # Tendencia Mensual de Apertura de OTs
        # Gráfico de línea: evolución mensual de creación de OTs
        df_linea = df_filtrado.groupby("Mes de creación").size().reset_index(name="Cantidad de OTs")
        fig_linea = px.line(
            df_linea,
            x="Mes de creación",
            y="Cantidad de OTs",
            text="Cantidad de OTs",
            template="plotly_white",
            markers=True,
            color_discrete_sequence=["#0F4C81"],
            title="Tendencia Mensual de Apertura de OTs"
        )
        fig_linea.update_traces(textposition="top center")
        st.plotly_chart(fig_linea, use_container_width=True)
        
        # Datos específicos para la tabla: registros agrupados por mes
        datos_tabla_activa = df_filtrado[["ID de Orden de Trabajo", "Mes de creación", "Estado", "Responsable"]].copy()
        datos_tabla_activa = datos_tabla_activa.sort_values("Mes de creación")
        columnas_tabla_dinamica = ["ID de Orden de Trabajo", "Mes de creación", "Estado", "Responsable"]

    # =========================================================================
    # TABLA DE DATOS DINÁMICA (TERCER BLOQUE)
    # =========================================================================
    st.markdown("---")
    st.subheader("📋 Datos Fuente del Gráfico Activo")
    st.caption(f"La tabla a continuación contiene los datos que alimentan el gráfico '{st.session_state.grafico_activo}'.")

    if datos_tabla_activa is not None:
        st.dataframe(datos_tabla_activa[columnas_tabla_dinamica], use_container_width=True, hide_index=True)
    else:
        st.warning("No hay datos disponibles para la tabla.")


if __name__ == "__main__":
    main()
