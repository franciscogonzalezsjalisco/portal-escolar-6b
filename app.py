import streamlit as st
import pandas as pd
import requests
import time
from urllib.parse import quote

# 1. CONFIGURACIÓN DE PÁGINA (DEBE SER LO PRIMERO)
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

# --- 2. INICIALIZAR MEMORIA (SOLUCIÓN AL ERROR) ---
if 'pantalla' not in st.session_state:
    st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state:
    st.session_state.semana_activa = None
if 'matricula_guardada' not in st.session_state:
    st.session_state.matricula_guardada = ""

# --- ENLACES DE IMÁGENES ---
URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"

# 3. CSS PARA MODO OSCURO Y BOTONES VIBRANTES
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("{URL_FONDO}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stButton > button {{
        width: 100%; height: 75px; border-radius: 15px;
        font-weight: 900; font-size: 18px; color: white !important;
        border: 2px solid rgba(255,255,255,0.2); margin-bottom: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }}
    h1, h2, h3, p, label, .stMarkdown {{ color: white !important; }}
    input {{ background-color: white !important; color: black !important; border-radius: 8px !important; }}
    </style>
    """, unsafe_allow_html=True)

# 4. FUNCIONES DE DATOS
@st.cache_data(ttl=300)
def obtener_nombres_hojas(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        xls = pd.ExcelFile(url, engine='openpyxl')
        return xls.sheet_names
    except: return ["S1 Enero"]

@st.cache_data(ttl=0) 
def cargar_datos(nombre_hoja):
    SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={int(time.time())}"
    data = pd.read_csv(url)
    data.columns = [str(col).strip() for col in data.columns]
    return data

SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"
listado_hojas = obtener_nombres_hojas(SHEET_ID)

# --- P
