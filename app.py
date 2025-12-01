import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Muestreo Wellboat",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# ESTILOS CSS
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    .main { padding: 0rem 1rem; }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚢 Dashboard de Muestreo Wellboat")
st.markdown("---")

# -----------------------------------------------------------------------------
# FUNCIÓN PARA CARGAR DATOS
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        st.info("ℹ️ Usando datos de ejemplo")

        data = {
            'FOLIO': ['F001', 'F002', 'F003', 'F004', 'F005', 'F006', 'F007', 'F008', 'F009', 'F010'],
            'FECHA MUESTREO': ['2024-01-15', '2024-01-20', '2024-02-10', '2024-02-15', '2024-03-05', 
                               '2024-03-18', '2024-04-12', '2024-04-25', '2024-05-08', '2024-05-20'],
            'WELLBOAT': ['WB-Alpha', 'WB-Beta', 'WB-Alpha', 'WB-Gamma', 'WB-Beta', 
                        'WB-Alpha', 'WB-Gamma', 'WB-Beta', 'WB-Alpha', 'WB-Gamma'],
            'ARMADOR': ['Armador A', 'Armador B', 'Armador A', 'Armador C', 'Armador B',
                       'Armador A', 'Armador C', 'Armador B', 'Armador A', 'Armador C'],
            'MUESTREADOR': ['Juan Pérez', 'María López', 'Juan Pérez', 'Pedro Silva', 'María López',
                           'Juan Pérez', 'Pedro Silva', 'María López', 'Juan Pérez', 'Pedro Silva'],
            'ANALISTA': ['Ana García', 'Carlos Ruiz', 'Ana García', 'Laura Díaz', 'Carlos Ruiz',
                        'Ana García', 'Laura Díaz', 'Carlos Ruiz', 'Ana García', 'Laura Díaz'],
            'LAT': [-41.4693, -41.5000, -41.4800, -41.4500, -41.5100, 
                   -41.4600, -41.4750, -41.5050, -41.4650, -41.4850],
            'LON': [-72.9424, -73.0000, -72.9500, -72.9300, -73.0100,
                   -72.9400, -72.9450, -73.0050, -72.9350, -72.9550],
            'RESULTADO': ['Positivo', 'Negativo', 'Positivo', 'Negativo', 'Positivo',
                         'Negativo', 'Positivo', 'Negativo', 'Positivo', 'Negativo'],
            'TIPO MUESTREO': ['Rutina', 'Especial', 'Rutina', 'Rutina', 'Especial',
                             'Rutina', 'Especial', 'Rutina', 'Rutina', 'Especial'],
            'DIA': [15, 20, 10, 15, 5, 18, 12, 25, 8, 20],
            'MES': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
            'AÑO': [2024] * 10
        }

        df = pd.DataFrame(data)

    df['FECHA MUESTREO'] = pd.to_datetime(df['FECHA MUESTREO'])
    df['MES_NOMBRE'] = df['FECHA MUESTREO'].dt.strftime('%B %Y')

    return df

# -----------------------------------------------------------------------------
# SIDEBAR: CARGA DE DATOS Y FILTROS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("📂 Carga de Datos")
    uploaded_file = st.file_uploader(
        "Sube tu archivo CSV",
        type=['csv'],
        help="Debe incluir: FOLIO, FECHA MUESTREO, WELLBOAT, ARMADOR, etc."
    )
    if uploaded_file:
        st.success("Archivo cargado correctamente")

df = load_data(uploaded_file)

with st.sidebar:
    st.markdown("---")
    st.header("🔍 Filtros")

    wellboats = ['Todos'] + sorted(df['WELLBOAT'].unique().tolist())
    selected_wellboat = st.selectbox("Wellboat", wellboats)

    armadores = ['Todos'] + sorted(df['ARMADOR'].unique().tolist())
    selected_armador = st.selectbox("Armador", armadores)

    resultados = ['Todos'] + sorted(df['RESULTADO'].unique().tolist())
    selected_resultado = st.selectbox("Resultado", resultados)

    tipos = ['Todos'] + sorted(df['TIPO MUESTREO'].unique().tolist())
    selected_tipo = st.selectbox("Tipo de Muestreo", tipos)

    st.markdown("**Rango de Fechas**")
    fecha_min = df['FECHA MUESTREO'].min().date()
    fecha_max = df['FECHA MUESTREO'].max().date()

    fecha_inicio = st.date_input("Desde", fecha_min)
    fecha_fin = st.date_input("Hasta", fecha_max)

# -----------------------------------------------------------------------------
# APLICAR FILTROS
# -----------------------------------------------------------------------------
df_filtered = df.copy()

if selected_wellboat != 'Todos':
    df_filtered = df_filtered[df_filtered['WELLBOAT'] == selected_wellboat]

if selected_armador != 'Todos':
    df_filtered = df_filtered[df_filtered['ARMADOR'] == selected_armador]

if selected_resultado != 'Todos':
    df_filtered = df_filtered[df_filtered['RESULTADO'] == selected_resultado]

if selected_tipo != 'Todos':
    df_filtered = df_filtered[df_filtered['TIPO MUESTREO'] == selected_tipo]

df_filtered = df_filtered[
    (df_filtered['FECHA MUESTREO'].dt.date >= fecha_inicio) &
    (df_filtered['FECHA MUESTREO'].dt.date <= fecha_fin)
]

# -----------------------------------------------------------------------------
# KPIs
# -----------------------------------------------------------------------------
st.header("📊 Indicadores Clave")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Muestras", len(df_filtered))

with col2:
    st.metric("Wellboats Únicos", df_filtered['WELLBOAT'].nunique())

with col3:
    positivos = df_filtered[df_filtered['RESULTADO'] == 'Positivo'].shape[0]
    pct_pos = positivos / len(df_filtered) * 100 if len(df_filtered) else 0
    st.metric("Resultados Positivos", positivos, f"{pct_pos:.1f}%")

with col4:
    negativos = df_filtered[df_filtered['RESULTADO'] == 'Negativo'].shape[0]
    pct_neg = negativos / len(df_filtered) * 100 if len(df_filtered) else 0
    st.metric("Resultados Negativos", negativos, f"{pct_neg:.1f}%")

st.markdown("---")

# -----------------------------------------------------------------------------
# GRÁFICOS
# -----------------------------------------------------------------------------
if len(df_filtered) > 0:

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Resultados por Mes")
        df_mes = df_filtered.groupby(['MES_NOMBRE', 'RESULTADO']).size().reset_index(name='Cantid]()
