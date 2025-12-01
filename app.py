import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

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

st.title("🚢 Dashboard de Muestreo Wellboat (2016-2025)")
st.markdown("---")

# -----------------------------------------------------------------------------
# FUNCIÓN PARA CARGAR DATOS DEL ARCHIVO EXCEL
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        try:
            # Intentar leer como Excel
            df = pd.read_excel(uploaded_file)
        except:
            # Si falla, intentar como CSV
            df = pd.read_csv(uploaded_file)
    else:
        # Si no hay archivo, usar datos de ejemplo basados en la estructura proporcionada
        st.info("ℹ️ No se cargó ningún archivo. Por favor, sube el archivo Excel 'BDPROGRAMA_2016-2025.xlsx'")
        
        # Crear DataFrame vacío con la estructura correcta
        data = {
            'FOLIO': [],
            'FECHA MUESTREO': [],
            'WELLBOAT': [],
            'ARMADOR': [],
            'MUESTREADOR': [],
            'ANALISTA': [],
            'LAT': [],
            'LON': [],
            'RESULTADO': [],
            'TIPO MUESTREO': [],
            'DIA': [],
            'MES': [],
            'AÑO': []
        }
        
        df = pd.DataFrame(data)

    # Limpieza y transformación de datos
    if not df.empty:
        # Convertir fecha a datetime
        if 'FECHA MUESTREO' in df.columns:
            df['FECHA MUESTREO'] = pd.to_datetime(df['FECHA MUESTREO'], errors='coerce')
        
        # Crear columna de mes-año para agrupaciones
        df['MES_NOMBRE'] = df['FECHA MUESTREO'].dt.strftime('%B %Y')
        
        # Normalizar resultados (mayúsculas/minúsculas)
        if 'RESULTADO' in df.columns:
            df['RESULTADO'] = df['RESULTADO'].str.upper()
            
        # Normalizar tipo de muestreo
        if 'TIPO MUESTREO' in df.columns:
            df['TIPO MUESTREO'] = df['TIPO MUESTREO'].str.upper()
            
        # Rellenar valores NaN en columnas críticas
        if 'WELLBOAT' in df.columns:
            df['WELLBOAT'] = df['WELLBOAT'].fillna('NO ESPECIFICADO')
        if 'RESULTADO' in df.columns:
            df['RESULTADO'] = df['RESULTADO'].fillna('SIN DATO')
        if 'TIPO MUESTREO' in df.columns:
            df['TIPO MUESTREO'] = df['TIPO MUESTREO'].fillna('NO ESPECIFICADO')

    return df

# -----------------------------------------------------------------------------
# SIDEBAR: CARGA DE DATOS Y FILTROS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("📂 Carga de Datos")
    uploaded_file = st.file_uploader(
        "Sube tu archivo Excel/CSV",
        type=['xlsx', 'xls', 'csv'],
        help="Sube el archivo 'BDPROGRAMA_2016-2025.xlsx'"
    )
    
    if uploaded_file:
        st.success(f"✅ Archivo cargado: {uploaded_file.name}")
    
    st.markdown("---")
    st.header("🔍 Filtros")
    
    # Cargar datos
    df = load_data(uploaded_file)
    
    if not df.empty:
        # Filtro de Wellboat
        wellboats = ['TODOS'] + sorted(df['WELLBOAT'].dropna().unique().tolist())
        selected_wellboat = st.selectbox("Wellboat", wellboats)
        
        # Filtro de Resultado
        resultados = ['TODOS'] + sorted(df['RESULTADO'].dropna().unique().tolist())
        selected_resultado = st.selectbox("Resultado", resultados)
        
        # Filtro de Tipo de Muestreo
        tipos = ['TODOS'] + sorted(df['TIPO MUESTREO'].dropna().unique().tolist())
        selected_tipo = st.selectbox("Tipo de Muestreo", tipos)
        
        # Filtro por año
        if 'AÑO' in df.columns:
            años = ['TODOS'] + sorted(df['AÑO'].dropna().unique().astype(int).tolist())
            selected_año = st.selectbox("Año", años)
        
        st.markdown("**Rango de Fechas**")
        if 'FECHA MUESTREO' in df.columns and not df['FECHA MUESTREO'].isna().all():
            fecha_min = df['FECHA MUESTREO'].min()
            fecha_max = df['FECHA MUESTREO'].max()
            
            # Convertir a date para el date_input
            if pd.notna(fecha_min) and pd.notna(fecha_max):
                fecha_min = fecha_min.date()
                fecha_max = fecha_max.date()
                fecha_inicio = st.date_input("Desde", fecha_min)
                fecha_fin = st.date_input("Hasta", fecha_max)
            else:
                st.warning("No hay fechas válidas en los datos")
                fecha_inicio = st.date_input("Desde", datetime(2016, 1, 1).date())
                fecha_fin = st.date_input("Hasta", datetime(2025, 12, 31).date())
        else:
            st.warning("No hay columna de fechas en los datos")
            fecha_inicio = st.date_input("Desde", datetime(2016, 1, 1).date())
            fecha_fin = st.date_input("Hasta", datetime(2025, 12, 31).date())

# -----------------------------------------------------------------------------
# APLICAR FILTROS
# -----------------------------------------------------------------------------
if not df.empty:
    df_filtered = df.copy()
    
    # Aplicar filtros
    if selected_wellboat != 'TODOS':
        df_filtered = df_filtered[df_filtered['WELLBOAT'] == selected_wellboat]
    
    if selected_resultado != 'TODOS':
        df_filtered = df_filtered[df_filtered['RESULTADO'] == selected_resultado]
    
    if selected_tipo != 'TODOS':
        df_filtered = df_filtered[df_filtered['TIPO MUESTREO'] == selected_tipo]
    
    if 'AÑO' in df.columns and selected_año != 'TODOS':
        df_filtered = df_filtered[df_filtered['AÑO'] == selected_año]
    
    # Filtrar por rango de fechas
    if 'FECHA MUESTREO' in df.columns:
        try:
            fecha_inicio_dt = pd.to_datetime(fecha_inicio)
            fecha_fin_dt = pd.to_datetime(fecha_fin)
            df_filtered = df_filtered[
                (df_filtered['FECHA MUESTREO'] >= fecha_inicio_dt) &
                (df_filtered['FECHA MUESTREO'] <= fecha_fin_dt)
            ]
        except:
            st.warning("Error al filtrar por fechas")

# -----------------------------------------------------------------------------
# KPIs
# -----------------------------------------------------------------------------
st.header("📊 Indicadores Clave")

if not df.empty and len(df_filtered) > 0:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Muestras", len(df_filtered))
    
    with col2:
        st.metric("Wellboats Únicos", df_filtered['WELLBOAT'].nunique())
    
    with col3:
        if 'RESULTADO' in df_filtered.columns:
            positivos = df_filtered[df_filtered['RESULTADO'] == 'POSITIVO'].shape[0]
            pct_pos = positivos / len(df_filtered) * 100 if len(df_filtered) else 0
            st.metric("Resultados Positivos", positivos, f"{pct_pos:.1f}%")
    
    with col4:
        if 'RESULTADO' in df_filtered.columns:
            negativos = df_filtered[df_filtered['RESULTADO'] == 'NEGATIVO'].shape[0]
            pct_neg = negativos / len(df_filtered) * 100 if len(df_filtered) else 0
            st.metric("Resultados Negativos", negativos, f"{pct_neg:.1f}%")
else:
    st.warning("⚠️ No hay datos para mostrar. Por favor, sube un archivo válido.")

st.markdown("---")

# -----------------------------------------------------------------------------
# GRÁFICOS
# -----------------------------------------------------------------------------
if not df.empty and len(df_filtered) > 0:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Resultados por Mes")
        if 'RESULTADO' in df_filtered.columns and 'MES_NOMBRE' in df_filtered.columns:
            df_mes = df_filtered.groupby(['MES_NOMBRE', 'RESULTADO']).size().reset_index(name='Cantidad')
            
            # Filtrar solo POSITIVO y NEGATIVO para el gráfico
            df_mes = df_mes[df_mes['RESULTADO'].isin(['POSITIVO', 'NEGATIVO'])]
            
            if not df_mes.empty:
                fig = px.bar(df_mes, x='MES_NOMBRE', y='Cantidad', color='RESULTADO',
                           barmode='group', color_discrete_map={'POSITIVO': 'red', 'NEGATIVO': 'green'})
                fig.update_layout(xaxis_title='Mes', yaxis_title='Cantidad de Muestras')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de resultados por mes")
        else:
            st.info("Faltan columnas necesarias para el gráfico")
    
    with col2:
        st.subheader("📊 Resultados por Wellboat (Top 10)")
        if 'WELLBOAT' in df_filtered.columns and 'RESULTADO' in df_filtered.columns:
            # Contar por wellboat
            wellboat_counts = df_filtered['WELLBOAT'].value_counts().head(10)
            
            # Crear DataFrame para el gráfico
            top_wellboats = wellboat_counts.index.tolist()
            df_top = df_filtered[df_filtered['WELLBOAT'].isin(top_wellboats)]
            
            if not df_top.empty:
                # Agrupar por wellboat y resultado
                df_wellboat = df_top.groupby(['WELLBOAT', 'RESULTADO']).size().reset_index(name='Cantidad')
                
                # Filtrar solo POSITIVO y NEGATIVO
                df_wellboat = df_wellboat[df_wellboat['RESULTADO'].isin(['POSITIVO', 'NEGATIVO'])]
                
                if not df_wellboat.empty:
                    fig = px.bar(df_wellboat, x='WELLBOAT', y='Cantidad', color='RESULTADO',
                               barmode='stack', color_discrete_map={'POSITIVO': 'red', 'NEGATIVO': 'green'})
                    fig.update_layout(xaxis_title='Wellboat', yaxis_title='Cantidad de Muestras',
                                    xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay datos de resultados por wellboat")
            else:
                st.info("No hay datos para los wellboats seleccionados")
        else:
            st.info("Faltan columnas necesarias para el gráfico")
    
    st.markdown("---")
    
    # Gráfico de evolución temporal
    st.subheader("📅 Evolución Temporal de Muestras")
    if 'FECHA MUESTREO' in df_filtered.columns:
        # Agrupar por fecha (sin hora)
        df_filtered['FECHA'] = df_filtered['FECHA MUESTREO'].dt.date
        df_evo = df_filtered.groupby('FECHA').size().reset_index(name='Cantidad')
        
        if not df_evo.empty:
            fig = px.line(df_evo, x='FECHA', y='Cantidad',
                        title='Número de Muestras por Día')
            fig.update_layout(xaxis_title='Fecha', yaxis_title='Cantidad de Muestras')
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Distribución por tipo de muestreo
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("📋 Distribución por Tipo de Muestreo")
        if 'TIPO MUESTREO' in df_filtered.columns:
            tipo_counts = df_filtered['TIPO MUESTREO'].value_counts()
            
            if not tipo_counts.empty:
                fig = px.pie(values=tipo_counts.values, names=tipo_counts.index,
                           title='Tipos de Muestreo')
                st.plotly_chart(fig, use_container_width=True)
    
    with col4:
        st.subheader("📊 Distribución por Resultado")
        if 'RESULTADO' in df_filtered.columns:
            resultado_counts = df_filtered['RESULTADO'].value_counts()
            
            if not resultado_counts.empty:
                fig = px.pie(values=resultado_counts.values, names=resultado_counts.index,
                           title='Distribución de Resultados')
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # TABLA DE DATOS
    st.subheader("📋 Vista de Datos")
    
    # Seleccionar columnas para mostrar
    columnas_disponibles = ['FOLIO', 'FECHA MUESTREO', 'WELLBOAT', 'ARMADOR', 
                          'RESULTADO', 'TIPO MUESTREO', 'DIA', 'MES', 'AÑO']
    columnas_a_mostrar = [col for col in columnas_disponibles if col in df_filtered.columns]
    
    # Mostrar tabla con paginación
    if len(df_filtered) > 0:
        st.dataframe(
            df_filtered[columnas_a_mostrar].head(1000),  # Limitar a 1000 filas para rendimiento
            use_container_width=True,
            height=400
        )
        st.caption(f"Mostrando {min(1000, len(df_filtered))} de {len(df_filtered)} registros")
    else:
        st.info("No hay datos que coincidan con los filtros")

# -----------------------------------------------------------------------------
# INFORMACIÓN ADICIONAL
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("---")
    st.header("📊 Estadísticas")
    
    if not df.empty:
        st.metric("Total Registros", len(df))
        if 'WELLBOAT' in df.columns:
            st.metric("Wellboats Diferentes", df['WELLBOAT'].nunique())
        if 'RESULTADO' in df.columns:
            positivos_total = len(df[df['RESULTADO'] == 'POSITIVO'])
            st.metric("Positivos Totales", positivos_total)
        
        st.markdown("---")
        st.header("ℹ️ Información")
        st.info("""
        **Columnas disponibles:**
        - FOLIO: Identificador único
        - FECHA MUESTREO: Fecha de toma de muestra
        - WELLBOAT: Nombre del wellboat
        - RESULTADO: POSITIVO/NEGATIVO
        - TIPO MUESTREO: RECALADA/EMBARQUE
        """)

# Mensaje si no hay datos
if df.empty or len(df) == 0:
    st.error("""
    ⚠️ **No se encontraron datos.**
    
    Por favor:
    1. Sube el archivo Excel 'BDPROGRAMA_2016-2025.xlsx' usando el panel lateral
    2. Asegúrate de que el archivo tenga las columnas requeridas
    3. Verifica que el formato del archivo sea correcto (.xlsx, .xls o .csv)
    """)
