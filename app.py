import streamlit as st
import pandas as pd
import requests
import time
from urllib.parse import quote

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

# --- ENLACES DE IMÁGENES ---
URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
# URL_LOGO = "Aquí_va_tu_logo_si_lo_tienes"

# 2. CSS AVANZADO: COLORES VIBRANTES Y ADAPTABILIDAD
st.markdown(f"""
    <style>
    /* Forzar fondo y visibilidad */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("{URL_FONDO}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* Estilo base de los botones */
    .stButton > button {{
        width: 100%;
        height: 85px;
        border-radius: 15px;
        font-weight: 900;
        font-size: 20px;
        color: white !important; /* Texto siempre blanco */
        border: 2px solid rgba(255,255,255,0.3);
        margin-bottom: 15px;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}

    /* Evitar que el modo oscuro del cel cambie el color del texto */
    .stMarkdown, p, h1, h2, h3, h5, label {{
        color: white !important;
    }}
    
    /* Input de matrícula legible */
    input {{
        background-color: white !important;
        color: black !important;
        border-radius: 10px !important;
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

# --- LÓGICA DE NAVEGACIÓN ---
if 'pantalla' not in st.session_state:
    st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state:
    st.session_state.semana_activa = None

SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"
listado_hojas = obtener_nombres_hojas(SHEET_ID)

# --- PANTALLA 1: MENÚ VIBRANTE ---
if st.session_state.pantalla == 'inicio':
    st.title("🏫 Portal Escolar 6° B")
    st.write("### Selecciona la semana a consultar:")

    # Lista de colores vibrantes solicitados
    colores = ["#FF4B4B", "#1C83E1", "#28A745", "#FFD700", "#7D3CFF"] # Rojo, Azul, Verde, Amarillo, Violeta

    # Generar botones con colores cíclicos
    for i in range(0, len(listado_hojas), 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < len(listado_hojas):
                color = colores[idx % len(colores)]
                with cols[j]:
                    # Aplicamos el color específico a cada botón mediante un truco de CSS por ID
                    st.markdown(f"<style>div[data-testid='column']:nth-of-type({j+1}) button[key='{listado_hojas[idx]}'] {{ background-color: {color} !important; }}</style>", unsafe_allow_html=True)
                    if st.button(listado_hojas[idx], key=listado_hojas[idx]):
                        st.session_state.semana_activa = listado_hojas[idx]
                        st.session_state.pantalla = 'consulta'
                        st.rerun()

# --- PANTALLA 2: CONSULTA ---
else:
    st.markdown(f"## 📍 {st.session_state.semana_activa}")
    
    if st.button("⬅️ VOLVER AL MENÚ"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

    # (Aquí sigue tu lógica de cargar_datos y el input de matrícula)
    # He incluido un contenedor blanco para que los resultados se vean bien
    with st.container():
        st.markdown('<div style="background-color: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px;">', unsafe_allow_html=True)
        matricula_input = st.text_input("Introduce la matrícula:")
        # ... resto del código de búsqueda ...
        st.markdown('</div>', unsafe_allow_html=True)
