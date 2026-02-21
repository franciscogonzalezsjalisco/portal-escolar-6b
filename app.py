import streamlit as st
import pandas as pd
import time
from urllib.parse import quote
from fpdf import FPDF
from datetime import datetime
import pytz 
import requests

# 1. CONFIGURACIÓN E IDENTIDAD
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

NOMBRE_MAESTRO = "Profr. Francisco González"
PASS_MAESTRO = "6B2024" 
URL_ESCUDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/ESCUDO%20690%20(1).png"
URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"
URL_LOG_SCRIPT = "https://script.google.com/macros/s/AKfycbz7fq8UUTz4JwoghvrzIZjVOFed4uWjq2_VYJIkL3HKHcE_izHMSRLQcrefrPf7pho/exec"

if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'ID_USUARIO' not in st.session_state: st.session_state.ID_USUARIO = ""
if 'alumno_datos' not in st.session_state: st.session_state.alumno_datos = None

# 2. ESTILOS (AZUL MARINO Y BLANCO)
st.markdown(f"""
    <style>
    .stApp {{ background-color: white !important; background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url("{URL_FONDO}"); background-size: cover; }}
    h1, h2, h3, h4, p, label, span, div, .stSelectbox p {{ color: #1D3557 !important; font-family: 'Segoe UI', sans-serif; }}
    .banner-maestro {{ text-align: center; background: #1D3557; color: white !important; padding: 15px; border-radius: 12px; margin-bottom: 20px; font-weight: bold; }}
    div.stButton > button {{ background-color: white !important; color: #1D3557 !important; border: 2px solid #1D3557 !important; width: 100% !important; border-radius: 12px !important; font-weight: 900; height: 50px; }}
    .tabla-container {{ background: white; padding: 15px; border-radius: 15px; border: 2px solid #1D3557; margin-top: 15px; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown(f'<div class="banner-maestro">🏫 {NOMBRE_MAESTRO} <br> <span style="color:white; font-size: 0.8rem;">6° B - Control Escolar Digital</span></div>', unsafe_allow_html=True)

# 3. FUNCIONES
def registrar_en_bitacora(matricula, nombre, semana, accion):
    try:
        payload = {
            "fecha": datetime.now(pytz.timezone('America/Mexico_City')).strftime("%d/%m/%Y %H:%M:%S"),
            "matricula": str(matricula), "nombre": str(nombre), "semana": str(semana), "accion": str(accion)
        }
        requests.post(URL_LOG_SCRIPT, json=payload, timeout=5)
    except: pass

def procesar_valor(val):
    v_str = str(val).strip().upper()
    if v_str in ['NAN', '', '0', '0.0', 'FALSE', 'FALSO']: return "❌ Pendiente"
    if v_str in ['1', '1.0', 'TRUE', 'VERDADERO']: return "✅ Completado"
    return str(val)

def crear_hoja_alumno_pdf(pdf, datos, semana, es_grupal=False):
    pdf.add_page()
    nombre_full = f"{datos.get('NOMBRE', '')} {datos.get('PATERNO', '')} {datos.get('MATERNO', '')}".strip()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(29, 53, 87)
    pdf.cell(0, 10, f"REPORTE ESCOLAR: {nombre_full}", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, f"Semana: {semana} | Maestro: {NOMBRE_MAESTRO}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_fill_color(29, 53, 87); pdf.set_text_color(255, 255, 255)
    pdf.cell(140, 8, " ACTIVIDAD", border=1, fill=True)
    pdf.cell(50, 8, " ESTADO", border=1, fill=True, ln=True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 9)
    omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    for k, v in datos.items():
        if k.upper() not in omitir and not str(k).startswith('Unnamed'):
            pdf.cell(140, 7, f" {str(k)[:75]}", border=1)
            pdf.cell(50, 7, f" {procesar_valor(v).replace('❌ ','').replace('✅ ','')}", border=1, ln=True)
    
    if not es_grupal:
        pdf.ln(10); pdf.set_font("Helvetica", "I", 8); pdf.set_text_color(100, 100, 100)
        ts = datetime.now(pytz.timezone('America/Mexico_City')).strftime("%d/%m/%Y %H:%M:%S")
        pdf.multi_cell(0, 5, f"Descarga oficial: {ts} hrs.\nMatrícula: {datos.get('MATRICULA','')}", align='C')

@st.cache_data(ttl=60)
def obtener_nombres_hojas(sid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=xlsx"
        xls = pd.ExcelFile(url, engine='openpyxl')
        return xls.sheet_names
    except: return ["Semana 1"]

def cargar_datos(nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={int(time.time())}"
    return pd.read_csv(url)

# --- FLUJO DE PANTALLAS ---
listado_hojas = obtener_nombres_hojas(SHEET_ID)

if st.session_state.pantalla == 'inicio':
    c1, c2, c3 = st.columns([1, 0.6, 1])
    with c2: st.image(URL_ESCUDO, use_container_width=True)
    st.markdown("<h4 style='text-align: center;'>Selecciona la semana</h4>", unsafe_allow_html=True)
    for i in range(0, len(listado_hojas), 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < len(listado_hojas):
                if cols[j].button(listado_hojas[idx], key=f"btn_{idx}"):
                    st.session_state.semana_activa = listado_hojas[idx]
                    st.session_state.pantalla = 'matricula'; st.rerun()
    
    st.markdown("---")
    with st.expander("🔐 Acceso Maestro"):
        pw = st.text_input("Contraseña:", type="password")
        if pw == PASS_MAESTRO:
            sem_m = st.selectbox("Semana para reporte grupal:", listado_hojas)
            if
