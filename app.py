import streamlit as st
import pandas as pd
import requests
import time
from urllib.parse import quote

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

# --- ENLACES DE IMÁGENES ---
URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"

# 2. CSS PARA MODO OSCURO Y COLORES VIBRANTES
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
    SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={int(time.time())}"
    data = pd.read_csv(url)
    data.columns = [str(col).strip() for col in data.columns]
    return data

# --- LÓGICA DE NAVEGACIÓN ---
if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None

SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"
listado_hojas = obtener_nombres_hojas(SHEET_ID)

# --- PANTALLA 1: MENÚ INICIAL ---
if st.session_state.pantalla == 'inicio':
    st.title("🏫 Portal Escolar 6° B")
    st.markdown("### Selecciona la semana:")
    
    colores = ["#FF4B4B", "#1C83E1", "#28A745", "#FFD700", "#7D3CFF"]
    
    for i in range(0, len(listado_hojas), 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < len(listado_hojas):
                nombre_h = listado_hojas[idx]
                color = colores[idx % len(colores)]
                with cols[j]:
                    st.markdown(f'<style>div[data-testid="column"]:nth-of-type({j+1}) button[key="{nombre_h}"] {{ background-color: {color} !important; }}</style>', unsafe_allow_html=True)
                    if st.button(nombre_h, key=nombre_h):
                        st.session_state.semana_activa = nombre_h
                        st.session_state.pantalla = 'consulta'
                        st.rerun()

# --- PANTALLA 2: CONSULTA Y RESULTADOS ---
else:
    st.markdown(f"## 📍 {st.session_state.semana_activa}")
    if st.button("⬅️ VOLVER AL MENÚ"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

    # CARGAR DATOS DE LA SEMANA SELECCIONADA
    df = cargar_datos(st.session_state.semana_activa)
    
    matricula_input = st.text_input("Ingresa la matrícula del alumno:", placeholder="Ej. 18066902")

    if matricula_input:
        col_mat = [c for c in df.columns if "MATRICULA" in c.upper()]
        if col_mat:
            # Limpiar datos para la búsqueda
            df['MAT_BUSCAR'] = df[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
            fila = df[df['MAT_BUSCAR'] == matricula_input.strip()]

            if not fila.empty:
                datos = fila.iloc[0]
                st.success(f"✅ **{datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}**")
                
                # Formatear tabla de resultados
                columnas_omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'MAT_BUSCAR', 'ALUMNO_COMPLETO']
                resumen = fila.drop(columns=[c for c in columnas_omitir if c in fila.columns]).T
                resumen.columns = ["Estado"]

                def aplicar_estilo(val):
                    v = str(val).upper().strip()
                    if v in ['0', '0.0', 'FALSE', 'NAN', '']: return "❌ Pendiente"
                    if v in ['1', '1.0', 'TRUE']: return "✅ OK"
                    return val

                resumen["Estado"] = resumen["Estado"].apply(aplicar_estilo)
                st.table(resumen)
            else:
                st.error("Matrícula no encontrada.")
