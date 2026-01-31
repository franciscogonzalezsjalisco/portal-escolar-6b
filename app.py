import streamlit as st
import pandas as pd
import requests
import time
from urllib.parse import quote

# 1. CONFIGURACIÓN TÉCNICA Y ESTÉTICA
st.set_page_config(
    page_title="Portal Escolar 6°B", 
    layout="wide", # Usamos wide para mejor adaptabilidad
    initial_sidebar_state="collapsed"
)

# Estilo personalizado para botones y tablas
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #f0f2f6;
        transition: 0.3s;
    }
    .stButton > button:hover {
        border-color: #673ab7;
        color: #673ab7;
    }
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 calc(25% - 1rem) !important;
        min-width: 150px !important;
    }
    </style>
    """, unsafe_allow_html=True)

SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

@st.cache_data(ttl=300)
def obtener_nombres_hojas(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        xls = pd.ExcelFile(url, engine='openpyxl')
        return xls.sheet_names
    except:
        return ["S1 Enero"]

@st.cache_data(ttl=0) 
def cargar_datos(nombre_hoja):
    t = int(time.time())
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={t}"
    data = pd.read_csv(url)
    data.columns = [str(col).strip() for col in data.columns]
    return data

def registrar_consulta_bitacora(matricula, hoja):
    FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfBv6p1-S-zL3Q6X_mF-nS_W7fXG8-b-K_V-z-qZ-B-w-Z-fQ/formResponse"
    payload = {"entry.1768815482": str(matricula), "entry.499470000": str(hoja)}
    try: requests.post(FORM_URL, data=payload, timeout=2)
    except: pass

# --- INTERFAZ PRINCIPAL ---
st.title("🏫 Portal Escolar 6° B")
st.markdown("##### Selecciona la semana que deseas consultar:")

# Inicializar la semana en el estado de la sesión si no existe
if 'semana_activa' not in st.session_state:
    st.session_state.semana_activa = None

listado_hojas = obtener_nombres_hojas(SHEET_ID)

# Crear fila de botones adaptativos
cols = st.columns(len(listado_hojas))
for i, nombre_hoja in enumerate(listado_hojas):
    if cols[i].button(nombre_hoja):
        st.session_state.semana_activa = nombre_hoja

# Solo mostrar buscador si hay una semana seleccionada
if st.session_state.semana_activa:
    st.markdown(f"### 📍 Consultando: **{st.session_state.semana_activa}**")
    
    df = cargar_datos(st.session_state.semana_activa)
    
    # Campo de matrícula con mejor diseño
    matricula_input = st.text_input("Introduce la matrícula del alumno:", key="mat", help="La matrícula debe ser la oficial del registro.")

    if matricula_input:
        col_mat = [c for c in df.columns if "MATRICULA" in c.upper()]
        
        if col_mat:
            df['MAT_BUSCAR'] = df[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
            fila = df[df['MAT_BUSCAR'] == matricula_input.strip()]

            if not fila.empty:
                datos_alumno = fila.iloc[0]
                nombre_completo = f"{datos_alumno.get('NOMBRE', '')} {datos_alumno.get('PATERNO', '')}"
                st.success(f"✅ Alumno encontrado: **{nombre_completo}**")
                
                registrar_consulta_bitacora(matricula_input, st.session_state.semana_activa)
                
                # Formateo de tabla
                columnas_omitir = ['NOMBRE', 'PATERNO', 'MATERNO''MATRICULA', 'MAT_BUSCAR', 'ALUMNO_COMPLETO']
                alumno_tabla = fila.drop(columns=[c for c in columnas_omitir if c in fila.columns])
                resumen = alumno_tabla.T
                resumen.columns = ["Estado"]

                def formatear(val, nombre_fila):
                    v_str = str(val).upper().strip()
                    if "CALIFICACIÓN" in str(nombre_fila).upper():
                        try: return f"{float(val):.1f}", 'background-color: #E3F2FD; font-weight: bold; color: #1565C0;'
                        except: return val, ''
                    if v_str in ['0', '0.0', 'FALSE', 'FALSO', 'NAN', '', '0']:
                        return "❌ Pendiente", 'background-color: #ffcccc; color: #990000; font-weight: bold;'
                    if v_str in ['1', '1.0', 'TRUE', 'VERDADERO']:
                        return "✅ Completado", 'background-color: #ccffcc; color: #006600;'
                    return str(val).replace('.0', ''), ''

                tabla_estilo = resumen.copy()
                estilos = []
                for n_fila, row in resumen.iterrows():
                    texto, css = formatear(row["Estado"], n_fila)
                    tabla_estilo.at[n_fila, "Estado"] = texto
                    estilos.append(css)

                st.table(tabla_estilo.style.apply(lambda x: estilos, axis=0))
            else:
                st.error("Matrícula no encontrada. Revisa que sea correcta.")
else:
    st.info("👆 Por favor, selecciona una semana arriba para comenzar.")

# Pie de página discreto
st.markdown("---")
st.caption("Si no ves datos actualizados, pulsa el botón de la semana nuevamente.")
