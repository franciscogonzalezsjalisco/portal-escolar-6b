import streamlit as st
import pandas as pd
import ssl
from urllib.parse import quote

# 1. CONFIGURACIÓN INICIAL
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

# 2. IDENTIFICACIÓN DEL DOCUMENTO
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"
MIS_HOJAS = ["S1 Enero", "S2 Enero", "S3 Enero", "S1 Febrero"]

@st.cache_data(ttl=300)
def cargar_datos(nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}"
    data = pd.read_csv(url)
    data.columns = [str(col).strip() for col in data.columns]
    return data

try:
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("📅 Ciclo Escolar")
        hoja_sel = st.selectbox("Selecciona la semana:", MIS_HOJAS)
        st.divider()
        st.info(f"Semana activa: {hoja_sel}")

    df = cargar_datos(hoja_sel)

    st.title("🏫 Portal de Consulta - 6° B")
    st.subheader(f"📍 Reporte: {hoja_sel}")
    st.markdown("---")

    # 3. SEGURIDAD: CONSULTA POR MATRÍCULA
    matricula_input = st.text_input("Ingresa la matrícula del alumno:", placeholder="Ej. 18066902")

    if matricula_input:
        # Buscamos la columna de matrícula (flexible a mayúsculas/minúsculas)
        col_mat = [c for c in df.columns if "MATRICULA" in c.upper()]
        
        if col_mat:
            # Limpiamos la columna matrícula para comparar correctamente
            df['MAT_BUSCAR'] = df[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
            fila = df[df['MAT_BUSCAR'] == matricula_input.strip()]

            if not fila.empty:
                datos_alumno = fila.iloc[0]
                # Obtenemos nombre y apellido para el encabezado
                nombre = f"{datos_alumno.get('NOMBRE', '')} {datos_alumno.get('PATERNO', '')}"
                st.success(f"Información de: **{nombre}**")
                
                # 4. TABLA DE RESULTADOS (Omitiendo datos ya mencionados)
                # Definimos qué columnas NO queremos mostrar en la tabla detallada
                columnas_a_omitir = [
                    'NOMBRE', 'PATERNO', 'MATRICULA', 'MAT_BUSCAR', 
                    'ALUMNO_COMPLETO', 'MAT_STR', 'MATRICULA_STR'
                ]
                
                # Filtramos la fila para quitar esas columnas
                alumno_tabla = fila.drop(columns=[c for c in columnas_a_omitir if c in fila.columns])
                
                resumen = alumno_tabla.T
                resumen.columns = ["Estado"]

                def formatear(val, nombre_fila):
                    v_str = str(val).upper().strip()
                    
                    # Calificación Semanal con 1 decimal
                    if "CALIFICACIÓN SEMANAL" in str(nombre_fila).upper():
                        try:
                            return f"{float(val):.1f}", 'background-color: #E3F2FD; font-weight: bold; color: #1565C0;'
                        except:
                            return val, ''

                    # Iconos para tareas
                    if v_str in ['0', '0.0', 'FALSE', 'FALSO', 'NAN', '', '0']:
                        return "❌ Pendiente", 'background-color: #ffcccc; color: #990000; font-weight: bold;'
                    if v_str in ['1', '1.0', 'TRUE', 'VERDADERO']:
                        return "✅ Completado", 'background-color: #ccffcc; color: #006600;'
                    
                    return str(val).replace('.0', ''), ''

                tabla_estilo = resumen.copy()
                estilos = []
                
                for n_fila, row in resumen.iterrows():
