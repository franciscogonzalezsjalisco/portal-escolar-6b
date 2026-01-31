import streamlit as st
import pandas as pd
import requests
import time
from urllib.parse import quote

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Portal Escolar 6°B", layout="wide")

# --- ENLACE DIRECTO DE GITHUB ---
URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
URL_LOGO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/ESCUDO 690 (1).png"

# 2. DISEÑO CSS PERSONALIZADO (BOTONES EN FILA DOBLE Y COLORES)
st.markdown(f"""
    <style>
    /* Fondo de la aplicación */
    .stApp {{
        background: linear-gradient(rgba(255,255,255,0.8), rgba(255,255,255,0.8)), url("{URL_FONDO}");
        background-size: cover;
    }}
    
    /* Contenedor de botones cuadrícula */
    .grid-container {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 15px;
        padding: 10px;
    }}
    
    /* Estilo de botones de semana */
    .stButton > button {{
        height: 80px;
        border-radius: 15px;
        font-size: 18px;
        font-weight: bold;
        color: white;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. FUNCIONES DE DATOS
@st.cache_data(ttl=300)
def obtener_nombres_hojas(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        xls = pd.ExcelFile(url, engine='openpyxl')
        return xls.sheet_names
    except: return ["S1 Enero"]

@st.cache_data(ttl=0) 
def cargar_datos(nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={int(time.time())}"
    data = pd.read_csv(url)
    data.columns = [str(col).strip() for col in data.columns]
    return data

# --- LÓGICA DE NAVEGACIÓN ---
if 'pantalla' not in st.session_state:
    st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state:
    st.session_state.semana_activa = None

listado_hojas = obtener_nombres_hojas("1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM")

# --- PANTALLA 1: INICIO ---
if st.session_state.pantalla == 'inicio':
    col_logo, col_tit = st.columns([1, 4])
    with col_logo:
        st.image(URL_LOGO, width=100)
    with col_tit:
        st.title("Portal Escolar 6° B")
        st.subheader("¡Bienvenido! Selecciona una semana:")

    # Colores para los botones
    colores = ["#4A90E2", "#50E3C2", "#F5A623", "#D0021B", "#9013FE", "#7ED321"]
    
    # Grid de botones (Fila doble en celular)
    filas = [listado_hojas[i:i + 2] for i in range(0, len(listado_hojas), 2)]
    
    for fila in filas:
        c1, c2 = st.columns(2)
        with c1:
            if st.button(fila[0], key=fila[0], use_container_width=True, help="Click para consultar"):
                st.session_state.semana_activa = fila[0]
                st.session_state.pantalla = 'consulta'
                st.rerun()
        with c2:
            if len(fila) > 1:
                if st.button(fila[1], key=fila[1], use_container_width=True):
                    st.session_state.semana_activa = fila[1]
                    st.session_state.pantalla = 'consulta'
                    st.rerun()

# --- PANTALLA 2: CONSULTA ---
else:
    # Encabezado con opción de volver o cambiar semana
    with st.expander(f"📅 Semana: {st.session_state.semana_activa} (Cambiar aquí)"):
        nueva_sem = st.selectbox("Selecciona otra semana:", listado_hojas, index=listado_hojas.index(st.session_state.semana_activa))
        if nueva_sem != st.session_state.semana_activa:
            st.session_state.semana_activa = nueva_sem
            st.rerun()
        if st.button("⬅️ Volver al Menú Principal"):
            st.session_state.pantalla = 'inicio'
            st.rerun()

    st.markdown("---")
    df = cargar_datos(st.session_state.semana_activa)
    
    matricula_input = st.text_input("📍 Ingresa la matrícula para ver resultados:", placeholder="Ej. 18066902")

    if matricula_input:
        col_mat = [c for c in df.columns if "MATRICULA" in c.upper()]
        if col_mat:
            df['MAT_BUSCAR'] = df[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
            fila = df[df['MAT_BUSCAR'] == matricula_input.strip()]

            if not fila.empty:
                st.success(f"✅ Alumno: **{fila.iloc[0].get('NOMBRE', '')} {fila.iloc[0].get('PATERNO', '')}**")
                
                # Mostrar tabla de resultados con el estilo anterior
                columnas_omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'MAT_BUSCAR', 'ALUMNO_COMPLETO']
                resumen = fila.drop(columns=[c for c in columnas_omitir if c in fila.columns]).T
                resumen.columns = ["Estado"]
                
                # ... (Aquí va la lógica de formatear() que ya teníamos) ...
                st.table(resumen) # Simplificado para el ejemplo
            else:
                st.error("Matrícula no encontrada.")
