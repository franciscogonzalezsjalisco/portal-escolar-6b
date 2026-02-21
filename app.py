import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
from datetime import datetime
import pytz
from urllib.parse import quote
import time

# 1. CONFIGURACIÓN E IDENTIDAD
st.set_page_config(page_title="Portal Escolar 6°B Urb. 690", layout="centered")

NOMBRE_MAESTRO = "Profr. Francisco González"
PASS_MAESTRO = "6B2024" 
URL_ESCUDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/ESCUDO%20690%20(1).png"
URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"
URL_LOG_SCRIPT = "https://script.google.com/macros/s/AKfycbwNGbSsky_dCyzvhf0WGfWj0mJMxR74Jrz2jmpIkJYLUDsH07cTCQjgbKO2E-TlaN_G/exec"

if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'ID_USUARIO' not in st.session_state: st.session_state.ID_USUARIO = ""
if 'alumno_datos' not in st.session_state: st.session_state.alumno_datos = None

# 2. --- ESTILOS DE DISEÑO ---
st.markdown(f"""
    <style>
    .stApp {{ 
        background-color: white !important; 
        background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url("{URL_FONDO}"); 
        background-size: cover; 
    }}
    
    h1, h2, h3, h4, p, label {{ color: #1D3557 !important; font-family: 'Segoe UI', sans-serif; }}

    .banner-maestro {{ 
        text-align: center; 
        background-color: #1D3557 !important; 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 25px; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }}
    
    .banner-maestro h2, .banner-maestro h3, .banner-maestro p {{
        color: #FFFFFF !important;
        margin: 5px 0px !important;
    }}

    div[data-baseweb="select"] {{
        border: 2px solid #1D3557 !important;
        border-radius: 12px !important;
    }}
    
    div.stButton > button {{ 
        background-color: white !important; 
        color: #1D3557 !important; 
        border: 2px solid #1D3557 !important; 
        border-radius: 12px !important; 
        font-weight: bold; 
    }}

    .streamlit-expanderHeader {{
        background-color: #F1F4F9 !important;
        border: 1px solid #1D3557 !important;
        border-radius: 10px !important;
    }}

    .footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.9);
        color: #1D3557;
        text-align: center;
        padding: 5px;
        font-size: 12px;
        font-weight: bold;
        border-top: 1px solid #1D3557;
        z-index: 999;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. --- ENCABEZADO PRINCIPAL ---
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.image(URL_ESCUDO, width=120)
st.markdown("<h2 style='margin-top:0;'>URBANA 690</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='color: #457B9D !important;'>6° Grado Grupo B</h4>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")

# 4. FUNCIONES
def registrar_en_bitacora(matricula, nombre, semana, accion):
    try:
        ts = datetime.now(pytz.timezone('America/Mexico_City')).strftime("%d/%m/%Y %H:%M:%S")
        params = {"fecha": ts, "matricula": str(matricula), "nombre": str(nombre), "semana": str(semana), "accion": str(accion)}
        headers = {"User-Agent": "Mozilla/5.0"}
        requests.get(URL_LOG_SCRIPT, params=params, headers=headers, timeout=10)
        st.toast(f"Registro exitoso: {accion}", icon="✅")
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
    pdf.cell(0, 10, f"REPORTE ES
