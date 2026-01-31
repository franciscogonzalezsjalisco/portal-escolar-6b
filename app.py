import streamlit as st
import pandas as pd
import requests
import time
from urllib.parse import quote

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

# --- INICIALIZAR MEMORIA ---
if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'matricula_guardada' not in st.session_state: st.session_state.matricula_guardada = ""

URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

# 2. CSS PARA BOTONES HOMOGÉNEOS Y VISIBILIDAD
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(255,255,255,0.75), rgba(255,255,255,0.75)), url("{URL_FONDO}");
        background-size: cover;
        background-attachment: fixed;
    }}
    /* Títulos claros en cualquier pantalla */
    h1, h2, h3, p, label {{
        color: #000000 !important;
        font-family: 'Arial', sans-serif;
    }}
    /* Botones con tamaño fijo y diseño uniforme */
    div.stButton > button {{
        width: 100% !important;
        height: 80px !important; /* Altura fija */
        border-radius: 12px !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: bold !important;
        text-transform: uppercase;
        border: 2px solid rgba(255,255,255,0.3) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        transition: 0.3s;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. FUNCIONES
@st.cache_data(ttl=60)
def obtener_nombres_hojas(sid):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=xlsx"
    try:
        xls = pd.ExcelFile(url, engine='openpyxl')
        return xls.sheet_names
    except: return ["S1 Enero"]

@st.cache_data(ttl=0) 
def cargar_datos(nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={int(time.time())}"
    return pd.read_csv(url)

listado_hojas = obtener_nombres_hojas(SHEET_ID)

# --- PANTALLA 1: INICIO ---
if st.session_state.pantalla == 'inicio':
    st.title("🏫 Portal Escolar 6° B")
    st.markdown("### 📅 Selecciona la semana")
    
    # Paleta de colores vibrantes
    colores = ["#E63946", "#457B9D", "#2A9D8F", "#F4A261", "#8338EC"]
    
    # Generar grid
    for i in range(0, len(listado_hojas), 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < len(listado_hojas):
                nombre_h = listado_hojas[idx]
                color_vibrante = colores[idx % len(colores)]
                with cols[j]:
                    # Inyección de color forzada por cada botón individualmente
                    st.markdown(f'<style>button[key="btn_{idx}"] {{ background-color: {color_vibrante} !important; }}</style>', unsafe_allow_html=True)
                    if st.button(nombre_h, key=f"btn_{idx}"):
                        st.session_state.semana_activa = nombre_h
                        st.session_state.pantalla = 'consulta'
                        st.rerun()
            
    st.markdown("---")
    if st.button("🔄 ACTUALIZAR LISTA", key="refresh"):
        st.cache_data.clear()
        st.rerun()

# --- PANTALLA 2: CONSULTA ---
else:
    st.markdown(f"## 📍 {st.session_state.semana_activa}")
    if st.button("⬅️ VOLVER AL MENÚ", key="volver"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

    df = cargar_datos(st.session_state.semana_activa)
    df.columns = [str(col).strip() for col in df.columns]
    
    mat_input = st.text_input("Introduce la matrícula:", value=st.session_state.matricula_guardada)
    st.session_state.matricula_guardada = mat_input

    if mat_input:
        col_mat = [c for c in df.columns if "MATRICULA" in c.upper()]
        if col_mat:
            df['BUSCAR'] = df[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
            fila = df[df['BUSCAR'] == mat_input.strip()]

            if not fila.empty:
                datos = fila.iloc[0]
                st.success(f"Alumno: {datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}")
                columnas_borrar = [c for c in df.columns if c.upper() in ['NOMBRE', 'PATERNO', 'MATRICULA', 'BUSCAR']]
                resumen = fila.drop(columns=columnas_borrar).T
                resumen.columns = ["Resultados"]
                st.table(resumen)
            else:
                st.error("Matrícula no encontrada.")
