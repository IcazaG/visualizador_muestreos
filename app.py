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
            # DEBUG: Mostrar información del archivo
            st.sidebar.info(f"📄 Archivo: {uploaded_file.name}")
            st.sidebar.info(f"📏 Tamaño: {uploaded_file.size / 1024:.1f} KB")
            
            # Leer el archivo basado en su extensión
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension in ['xlsx', 'xls']:
                # Leer Excel
                df = pd.read_excel(uploaded_file, engine='openpyxl')
                
                # DEBUG: Mostrar información de hojas
                excel_file = pd.ExcelFile(uploaded_file, engine='openpyxl')
                st.sidebar.info(f"📑 Hojas disponibles: {excel_file.sheet_names}")
                
                # Si hay múltiples hojas, usar la primera
                if len(excel_file.sheet_names) > 1:
                    st.sidebar.warning(f"Usando la hoja: '{excel_file.sheet_names[0]}'")
                    
            elif file_extension == 'csv':
                # Leer CSV
                df = pd.read_csv(uploaded_file)
            else:
                st.error(f"Formato no soportado: {file_extension}")
                return pd.DataFrame()
            
            # DEBUG: Mostrar información del DataFrame
            st.sidebar.success(f"✅ Datos cargados: {len(df)} filas, {len(df.columns)} columnas")
            st.sidebar.info(f"📋 Columnas: {list(df.columns)}")
            
            # Mostrar primeras filas para depuración
            with st.expander("🔍 Vista previa de datos (primeras 5 filas)", expanded=False):
                st.dataframe(df.head())
            
            # Verificar si el DataFrame está vacío
            if df.empty:
                st.error("⚠️ El DataFrame está vacío. Revisa el formato del archivo.")
                return df
            
            # Mostrar información de tipos de datos
            with st.expander("📊 Información de tipos de datos", expanded=False):
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())
            
            # Normalizar nombres de columnas (eliminar espacios extra, poner mayúsculas)
            df.columns = df.columns.str.strip()
            
            # Verificar columnas críticas
            required_columns = ['FOLIO', 'FECHA MUESTREO', 'WELLBOAT', 'RESULTADO']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"⚠️ Faltan columnas críticas: {missing_columns}")
                st.warning(f"Columnas disponibles: {list(df.columns)}")
                
                # Intentar encontrar columnas con nombres similares
                for missing_col in missing_columns:
                    similar_cols = [col for col in df.columns if missing_col.lower() in col.lower()]
                    if similar_cols:
                        st.info(f"Columnas similares a '{missing_col}': {similar_cols}")
            
            # Convertir fecha a datetime (manejar diferentes formatos)
            if 'FECHA MUESTREO' in df.columns:
                try:
                    df['FECHA MUESTREO'] = pd.to_datetime(df['FECHA MUESTREO'], errors='coerce')
                    
                    # Verificar cuántas fechas se convirtieron correctamente
                    valid_dates = df['FECHA MUESTREO'].notna().sum()
                    st.sidebar.info(f"📅 Fechas válidas: {valid_dates}/{len(df)}")
                    
                    if valid_dates == 0:
                        st.warning("No se pudieron convertir las fechas. Verifica el formato.")
                        
                        # Mostrar ejemplos de fechas problemáticas
                        date_samples = df['FECHA MUESTREO'].head().astype(str).tolist()
                        st.write(f"Ejemplos de fechas: {date_samples}")
                except Exception as e:
                    st.error(f"Error al convertir fechas: {e}")
            
            # Crear columna de mes-año para agrupaciones
            if 'FECHA MUESTREO' in df.columns and df['FECHA MUESTREO'].notna().any():
                df['MES_NOMBRE'] = df['FECHA MUESTREO'].dt.strftime('%B %Y')
            
            # Normalizar resultados (mayúsculas/minúsculas)
            if 'RESULTADO' in df.columns:
                df['RESULTADO'] = df['RESULTADO'].astype(str).str.strip().str.upper()
                
                # Mostrar distribución de resultados
                result_counts = df['RESULTADO'].value_counts()
                st.sidebar.info(f"📊 Resultados: {dict(result_counts)}")
            
            # Normalizar tipo de muestreo
            if 'TIPO MUESTREO' in df.columns:
                df['TIPO MUESTREO'] = df['TIPO MUESTREO'].astype(str).str.strip().str.upper()
            
            # Rellenar valores NaN en columnas críticas
            if 'WELLBOAT' in df.columns:
                df['WELLBOAT'] = df['WELLBOAT'].fillna('NO ESPECIFICADO')
                
                # Mostrar wellboats únicos
                unique_wellboats = df['WELLBOAT'].nunique()
                st.sidebar.info(f"🚢 Wellboats únicos: {unique_wellboats}")
            
            # Extraer año, mes, día si existen las columnas separadas
            if 'AÑO' not in df.columns and 'FECHA MUESTREO' in df.columns:
                df['AÑO'] = df['FECHA MUESTREO'].dt.year
            if 'MES' not in df.columns and 'FECHA MUESTREO' in df.columns:
                df['MES'] = df['FECHA MUESTREO'].dt.month
            if 'DIA' not in df.columns and 'FECHA MUESTREO' in df.columns:
                df['DIA'] = df['FECHA MUESTREO'].dt.day
            
            return df
            
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")
            import traceback
            st.error(f"Detalles del error: {traceback.format_exc()}")
            return pd.DataFrame()
    else:
        # Si no hay archivo, mostrar instrucciones
        st.info("""
        ### 📋 Instrucciones:
        1. Usa el panel lateral para subir tu archivo
        2. Aceptamos formatos: **.xlsx, .xls, .csv**
        3. El archivo debe contener al menos estas columnas:
           - FOLIO
           - FECHA MUESTREO
           - WELLBOAT
           - RESULTADO
           - TIPO MUESTREO
        """)
        return pd.DataFrame()

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
    
    st.markdown("---")
    
    # Cargar datos
    df = load_data(uploaded_file)
    
    if df is not None and not df.empty:
        st.header("🔍 Filtros")
        
        # Filtro de Wellboat
        if 'WELLBOAT' in df.columns:
            wellboats = ['TODOS'] + sorted(df['WELLBOAT'].dropna().unique().tolist())
            selected_wellboat = st.selectbox("Wellboat", wellboats)
        else:
            st.warning("No hay columna 'WELLBOAT' en los datos")
            selected_wellboat = 'TODOS'
        
        # Filtro de Resultado
        if 'RESULTADO' in df.columns:
            resultados = ['TODOS'] + sorted(df['RESULTADO'].dropna().unique().tolist())
            selected_resultado = st.selectbox("Resultado", resultados)
        else:
            st.warning("No hay columna 'RESULTADO' en los datos")
            selected_resultado = 'TODOS'
        
        # Filtro de Tipo de Muestreo
        if 'TIPO MUESTREO' in df.columns:
            tipos = ['TODOS'] + sorted(df['TIPO MUESTREO'].dropna().unique().tolist())
            selected_tipo = st.selectbox("Tipo de Muestreo", tipos)
        else:
            st.warning("No hay columna 'TIPO MUESTREO' en los datos")
            selected_tipo = 'TODOS'
        
        # Filtro por año
        if 'AÑO' in df.columns:
            años = ['TODOS'] + sorted(df['AÑO'].dropna().unique().astype(int).tolist())
            selected_año = st.selectbox("Año", años)
        else:
            selected_año = 'TODOS'
        
        # Filtro por rango de fechas
        st.markdown("**📅 Rango de Fechas**")
        if 'FECHA MUESTREO' in df.columns and df['FECHA MUESTREO'].notna().any():
            fecha_min = df['FECHA MUESTREO'].min().date()
            fecha_max = df['FECHA MUESTREO'].max().date()
            
            fecha_inicio = st.date_input("Desde", fecha_min)
            fecha_fin = st.date_input("Hasta", fecha_max)
            
            st.caption(f"Rango disponible: {fecha_min} a {fecha_max}")
        else:
            fecha_inicio = st.date_input("Desde", datetime(2016, 1, 1).date())
            fecha_fin = st.date_input("Hasta", datetime(2025, 12, 31).date())
        
        st.markdown("---")
        st.header("📊 Estadísticas")
        st.metric("Total Registros", len(df))
        
        if 'WELLBOAT' in df.columns:
            st.metric("Wellboats Diferentes", df['WELLBOAT'].nunique())
        
        if 'RESULTADO' in df.columns:
            positivos_total = len(df[df['RESULTADO'] == 'POSITIVO'])
            st.metric("Positivos Totales", positivos_total)

# -----------------------------------------------------------------------------
# APLICAR FILTROS
# -----------------------------------------------------------------------------
if df is not None and not df.empty:
    df_filtered = df.copy()
    
    # Contador inicial
    initial_count = len(df_filtered)
    
    # Aplicar filtros
    filters_applied = []
    
    if selected_wellboat != 'TODOS':
        df_filtered = df_filtered[df_filtered['WELLBOAT'] == selected_wellboat]
        filters_applied.append(f"Wellboat: {selected_wellboat}")
    
    if selected_resultado != 'TODOS':
        df_filtered = df_filtered[df_filtered['RESULTADO'] == selected_resultado]
        filters_applied.append(f"Resultado: {selected_resultado}")
    
    if selected_tipo != 'TODOS':
        df_filtered = df_filtered[df_filtered['TIPO MUESTREO'] == selected_tipo]
        filters_applied.append(f"Tipo: {selected_tipo}")
    
    if selected_año != 'TODOS' and 'AÑO' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['AÑO'] == selected_año]
        filters_applied.append(f"Año: {selected_año}")
    
    # Filtrar por rango de fechas
    if 'FECHA MUESTREO' in df_filtered.columns:
        try:
            fecha_inicio_dt = pd.to_datetime(fecha_inicio)
            fecha_fin_dt = pd.to_datetime(fecha_fin)
            
            df_filtered = df_filtered[
                (df_filtered['FECHA MUESTREO'] >= fecha_inicio_dt) &
                (df_filtered['FECHA MUESTREO'] <= fecha_fin_dt)
            ]
            filters_applied.append(f"Fechas: {fecha_inicio} a {fecha_fin}")
        except Exception as e:
            st.warning(f"Error al filtrar por fechas: {e}")
    
    # Mostrar información de filtros aplicados
    if filters_applied:
        st.sidebar.info(f"Filtros aplicados: {len(filters_applied)}")
        for filtro in filters_applied:
            st.sidebar.text(f"• {filtro}")
    
    final_count = len(df_filtered)
    st.sidebar.metric("Registros filtrados", final_count, delta=final_count-initial_count)

# -----------------------------------------------------------------------------
# SECCIÓN PRINCIPAL - VISUALIZACIONES
# -----------------------------------------------------------------------------
if df is not None and not df.empty:
    if len(df_filtered) > 0:
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
            if 'RESULTADO' in df_filtered.columns:
                positivos = df_filtered[df_filtered['RESULTADO'] == 'POSITIVO'].shape[0]
                pct_pos = positivos / len(df_filtered) * 100 if len(df_filtered) else 0
                st.metric("Resultados Positivos", positivos, f"{pct_pos:.1f}%")
        
        with col4:
            if 'RESULTADO' in df_filtered.columns:
                negativos = df_filtered[df_filtered['RESULTADO'] == 'NEGATIVO'].shape[0]
                pct_neg = negativos / len(df_filtered) * 100 if len(df_filtered) else 0
                st.metric("Resultados Negativos", negativos, f"{pct_neg:.1f}%")
        
        st.markdown("---")
        
        # -----------------------------------------------------------------------------
        # GRÁFICOS
        # -----------------------------------------------------------------------------
        if len(df_filtered) > 1:  # Necesitamos al menos 2 filas para gráficos significativos
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Resultados por Mes")
                if 'RESULTADO' in df_filtered.columns and 'MES_NOMBRE' in df_filtered.columns:
                    # Crear DataFrame para el gráfico
                    df_mes = df_filtered.copy()
                    df_mes = df_mes[df_mes['RESULTADO'].isin(['POSITIVO', 'NEGATIVO'])]
                    
                    if not df_mes.empty:
                        # Agrupar por mes y resultado
                        df_grouped = df_mes.groupby(['MES_NOMBRE', 'RESULTADO']).size().reset_index(name='Cantidad')
                        
                        # Ordenar por fecha
                        df_grouped['Fecha_Orden'] = pd.to_datetime(df_grouped['MES_NOMBRE'], format='%B %Y')
                        df_grouped = df_grouped.sort_values('Fecha_Orden')
                        
                        fig = px.bar(df_grouped, x='MES_NOMBRE', y='Cantidad', color='RESULTADO',
                                   barmode='group', 
                                   color_discrete_map={'POSITIVO': 'red', 'NEGATIVO': 'green'},
                                   category_orders={"MES_NOMBRE": df_grouped['MES_NOMBRE'].tolist()})
                        fig.update_layout(
                            xaxis_title='Mes',
                            yaxis_title='Cantidad de Muestras',
                            xaxis_tickangle=-45,
                            legend_title='Resultado'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No hay datos de POSITIVO/NEGATIVO para mostrar")
                else:
                    st.info("Faltan columnas para el gráfico de resultados por mes")
            
            with col2:
                st.subheader("📊 Top 10 Wellboats")
                if 'WELLBOAT' in df_filtered.columns:
                    # Contar muestras por wellboat
                    wellboat_counts = df_filtered['WELLBOAT'].value_counts().head(10)
                    
                    if not wellboat_counts.empty:
                        fig = px.bar(
                            x=wellboat_counts.index,
                            y=wellboat_counts.values,
                            labels={'x': 'Wellboat', 'y': 'Cantidad de Muestras'},
                            color=wellboat_counts.values,
                            color_continuous_scale='viridis'
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Mostrar tabla debajo
                        with st.expander("Ver tabla detallada", expanded=False):
                            st.dataframe(wellboat_counts.reset_index().rename(
                                columns={'index': 'Wellboat', 'WELLBOAT': 'Muestras'}
                            ))
                    else:
                        st.info("No hay datos de wellboats para mostrar")
            
            st.markdown("---")
            
            # Gráfico de evolución temporal
            st.subheader("📅 Evolución Temporal de Muestras")
            if 'FECHA MUESTREO' in df_filtered.columns:
                # Crear columna de fecha sin hora
                df_filtered['FECHA'] = df_filtered['FECHA MUESTREO'].dt.date
                
                # Agrupar por fecha
                df_evo = df_filtered.groupby('FECHA').size().reset_index(name='Cantidad')
                df_evo = df_evo.sort_values('FECHA')
                
                if len(df_evo) > 1:
                    fig = px.line(df_evo, x='FECHA', y='Cantidad',
                                title='Número de Muestras por Día',
                                markers=True)
                    fig.update_layout(
                        xaxis_title='Fecha',
                        yaxis_title='Cantidad de Muestras',
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Se necesitan al menos 2 fechas diferentes para el gráfico de evolución")
            
            st.markdown("---")
            
            # Distribución por tipo de muestreo y resultado
            col3, col4 = st.columns(2)
            
            with col3:
                st.subheader("📋 Distribución por Tipo de Muestreo")
                if 'TIPO MUESTREO' in df_filtered.columns:
                    tipo_counts = df_filtered['TIPO MUESTREO'].value_counts()
                    
                    if not tipo_counts.empty:
                        fig = px.pie(
                            values=tipo_counts.values,
                            names=tipo_counts.index,
                            title='Tipos de Muestreo',
                            hole=0.3
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with col4:
                st.subheader("📊 Distribución por Resultado")
                if 'RESULTADO' in df_filtered.columns:
                    resultado_counts = df_filtered['RESULTADO'].value_counts()
                    
                    if not resultado_counts.empty:
                        fig = px.pie(
                            values=resultado_counts.values,
                            names=resultado_counts.index,
                            title='Distribución de Resultados',
                            hole=0.3,
                            color=resultado_counts.index,
                            color_discrete_map={'POSITIVO': 'red', 'NEGATIVO': 'green'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # -----------------------------------------------------------------------------
            # TABLA DE DATOS
            # -----------------------------------------------------------------------------
            st.subheader("📋 Vista de Datos Filtrados")
            
            # Seleccionar columnas para mostrar
            columnas_disponibles = ['FOLIO', 'FECHA MUESTREO', 'WELLBOAT', 'ARMADOR', 
                                  'RESULTADO', 'TIPO MUESTREO', 'DIA', 'MES', 'AÑO']
            columnas_a_mostrar = [col for col in columnas_disponibles if col in df_filtered.columns]
            
            # Añadir columnas adicionales si existen
            additional_cols = [col for col in df_filtered.columns if col not in columnas_disponibles]
            columnas_a_mostrar.extend(additional_cols[:5])  # Limitar columnas adicionales
            
            if columnas_a_mostrar:
                # Mostrar tabla con opciones
                show_all = st.checkbox("Mostrar todos los datos", value=False)
                
                if show_all:
                    st.dataframe(
                        df_filtered[columnas_a_mostrar],
                        use_container_width=True,
                        height=500
                    )
                    st.caption(f"Mostrando {len(df_filtered)} registros")
                else:
                    # Mostrar solo las primeras filas
                    st.dataframe(
                        df_filtered[columnas_a_mostrar].head(100),
                        use_container_width=True,
                        height=400
                    )
                    st.caption(f"Mostrando 100 de {len(df_filtered)} registros. Marca 'Mostrar todos los datos' para ver todos.")
                
                # Opción para descargar datos filtrados
                csv = df_filtered[columnas_a_mostrar].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar datos filtrados (CSV)",
                    data=csv,
                    file_name="datos_filtrados.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No hay columnas para mostrar en la tabla")
        
        else:
            st.warning("⚠️ No hay suficientes datos filtrados para generar visualizaciones")
            st.info("Intenta ajustar los filtros o verifica que los datos tengan la estructura correcta.")
    
    else:
        st.warning("⚠️ No hay datos que coincidan con los filtros aplicados")
        st.info("""
        Sugerencias:
        1. Ajusta los filtros en el panel lateral
        2. Verifica que el rango de fechas sea correcto
        3. Intenta seleccionar 'TODOS' en algunos filtros
        """)

# -----------------------------------------------------------------------------
# INFORMACIÓN ADICIONAL
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("---")
    st.header("ℹ️ Ayuda")
    
    with st.expander("📖 Instrucciones de uso"):
        st.markdown("""
        1. **Sube el archivo** en el panel superior
        2. **Aplica filtros** según necesites
        3. **Visualiza los gráficos** y KPIs
        4. **Explora los datos** en la tabla inferior
        
        **Columnas requeridas:**
        - FOLIO
        - FECHA MUESTREO
        - WELLBOAT
        - RESULTADO
        - TIPO MUESTREO
        """)
    
    with st.expander("🔧 Solución de problemas"):
        st.markdown("""
        **Si no ves datos:**
        1. Verifica que el archivo tenga las columnas correctas
        2. Revisa que las fechas tengan formato válido
        3. Asegúrate de que los filtros no estén muy restrictivos
        
        **Si hay errores:**
        1. Revisa los mensajes en rojo
        2. Verifica el formato del archivo (.xlsx, .csv)
        3. Contacta al administrador si persiste
        """)

# Mensaje final si no hay datos
if df is None or (hasattr(df, 'empty') and df.empty):
    st.error("""
    ## ⚠️ No se pudieron cargar datos
    
    **Posibles causas:**
    1. No se ha subido ningún archivo
    2. El archivo está vacío o corrupto
    3. El formato del archivo no es compatible
    4. Faltan columnas críticas en los datos
    
    **Solución:**
    1. Asegúrate de subir un archivo en el panel lateral
    2. Verifica que el archivo contenga datos
    3. Usa los formatos soportados: .xlsx, .xls, .csv
    4. Revisa que el archivo tenga al menos las columnas FOLIO, FECHA MUESTREO, WELLBOAT, RESULTADO
    """)
    
    # Mostrar ejemplo de cómo debería verse el archivo
    with st.expander("📋 Ejemplo de estructura de datos", expanded=False):
        example_data = {
            'FOLIO': ['QLL-FAN-2016-1000', 'QLL-FAN-2016-1001'],
            'FECHA MUESTREO': ['2016-11-09 00:00:00', '2016-11-10 00:00:00'],
            'WELLBOAT': ['ORCA CHONO', 'RIO DULCE 1'],
            'ARMADOR': ['', ''],
            'MUESTREADOR': ['', ''],
            'ANALISTA': ['', ''],
            'LAT': ['', ''],
            'LON': ['', ''],
            'RESULTADO': ['NEGATIVO', 'NEGATIVO'],
            'TIPO MUESTREO': ['RECALADA', 'RECALADA'],
            'DIA': [9, 10],
            'MES': [11, 11],
            'AÑO': [2016, 2016]
        }
        example_df = pd.DataFrame(example_data)
        st.dataframe(example_df)
