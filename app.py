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
PASS_MAESTRO = "6B2024"  # <--- CAMBIA AQUÍ TU CONTRASEÑA
URL_ESCUDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/ESCUDO%20690%20(1).png"
URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"
URL_LOG_SCRIPT = "https://script.google.com/macros/s/AKfycbz7fq8UUTz4JwoghvrzIZjVOFed4uWjq2_VYJIkL3HKHcE_izHMSRLQcrefrPf7pho/exec"

if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'ID_USUARIO' not in st.session_state: st.session_state.ID_USUARIO = ""
if 'alumno_datos' not in st.session_state: st.session_state.alumno_datos = None

# 2. ESTILOS
st.markdown(f"""
    <style>
    .stApp {{ background-color: white !important; background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url("{URL_FONDO}"); background-size: cover; }}
    h1, h2, h3, h4, p, label, span, div {{ color: #1D3557 !important; font-family: 'Segoe UI', sans-serif; }}
    .banner-maestro {{ text-align: center; background: #1D3557; color: white !important; padding: 15px; border-radius: 12px; margin-bottom: 20px; font-weight: bold; }}
    div.stButton > button {{ background-color: white !important; color: #1D3557 !important; border: 2px solid #1D3557 !important; width: 100% !important; border-radius: 12px !important; font-weight: 900; }}
    .tabla-container {{ background: white; padding: 15px; border-radius: 15px; border: 2px solid #1D3557; margin-top: 15px; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown(f'<div class="banner-maestro">🏫 {NOMBRE_MAESTRO} <br> <span style="color:white; font-size: 0.8rem;">6° B - Control Escolar Digital</span></div>', unsafe_allow_html=True)

# 3. FUNCIONES DE GENERACIÓN DE PDF
def procesar_valor(val):
    v_str = str(val).strip().upper()
    if v_str in ['NAN', '', '0', '0.0', 'FALSE', 'FALSO']: return "Pendiente"
    if v_str in ['1', '1.0', 'TRUE', 'VERDADERO']: return "Completado"
    return str(val)

def crear_hoja_alumno(pdf, datos, semana):
    pdf.add_page()
    nombre_full = f"{datos.get('NOMBRE', '')} {datos.get('PATERNO', '')} {datos.get('MATERNO', '')}".strip()
    
    # Encabezado
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(29, 53, 87)
    pdf.cell(0, 10, f"REPORTE ESCOLAR: {nombre_full}", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, f"Semana: {semana} | Maestro: {NOMBRE_MAESTRO}", ln=True, align="C")
    pdf.ln(5)
    
    # Tabla
    pdf.set_fill_color(29, 53, 87)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(140, 8, " ACTIVIDAD", border=1, fill=True)
    pdf.cell(50, 8, " ESTADO", border=1, fill=True, ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    for k, v in datos.items():
        if k.upper() not in omitir and not str(k).startswith('Unnamed'):
            res = procesar_valor(v)
            pdf.cell(140, 7, f" {str(k)[:75]}", border=1)
            pdf.cell(50, 7, f" {res}", border=1, ln=True)

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

# --- PANTALLAS ---

if st.session_state.pantalla == 'inicio':
    c1, c2, c3 = st.columns([1, 0.6, 1])
    with c2: st.image(URL_ESCUDO, use_container_width=True)
    
    st.markdown("<h4 style='text-align: center;'>Selecciona la semana</h4>", unsafe_allow_html=True)
    listado_hojas = obtener_nombres_hojas(SHEET_ID)
    for i in range(0, len(listado_hojas), 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < len(listado_hojas):
                nombre_h = listado_hojas[idx]
                if cols[j].button(nombre_h, key=f"btn_{idx}"):
                    st.session_state.semana_activa = nombre_h
                    st.session_state.pantalla = 'matricula'
                    st.rerun()
    
    # SECCIÓN MAESTRO
    st.markdown("---")
    with st.expander("🔐 Acceso Exclusivo Maestro"):
        pw = st.text_input("Contraseña de administrador:", type="password")
        if pw == PASS_MAESTRO:
            semana_descarga = st.selectbox("Elegir semana para descargar todo el grupo:", listado_hojas)
            if st.button("🚀 GENERAR PDF DE TODO EL GRUPO"):
                with st.spinner("Procesando 30 alumnos... esto tomará unos segundos."):
                    df_todo = cargar_datos(semana_descarga)
                    pdf_master = FPDF()
                    for _, fila in df_todo.iterrows():
                        crear_hoja_alumno(pdf_master, fila.to_dict(), semana_descarga)
                    
                    pdf_bytes = bytes(pdf_master.output())
                    st.download_button(f"📥 DESCARGAR COMPILADO {semana_descarga}", 
                                       data=pdf_bytes, 
                                       file_name=f"Reporte_Grupal_{semana_descarga}.pdf", 
                                       mime="application/pdf")

elif st.session_state.pantalla == 'matricula':
    # (El código de la matrícula y resultados se mantiene igual que la versión anterior...)
    st.markdown(f"<h4 style='text-align: center;'>📍 {st.session_state.semana_activa}</h4>", unsafe_allow_html=True)
    mat_input = st.text_input("Ingresa la matrícula del alumno:", value=st.session_state.ID_USUARIO)
    if st.button("🔍 VER REPORTE"):
        if mat_input:
            st.session_state.ID_USUARIO = mat_input.strip()
            df = cargar_datos(st.session_state.semana_activa)
            df.columns = [str(col).strip() for col in df.columns]
            col_mat = [c for c in df.columns if "MATRICULA" in c.upper()]
            if col_mat:
                df['BUSCAR'] = df[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
                fila = df[df['BUSCAR'] == st.session_state.ID_USUARIO]
                if not fila.empty:
                    st.session_state.alumno_datos = fila.iloc[0].to_dict()
                    st.session_state.pantalla = 'resultados'
                    st.rerun()
                else: st.error("❌ No encontrada.")
    if st.button("⬅️ VOLVER"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

elif st.session_state.pantalla == 'resultados':
    # (Código de visualización de tabla de la versión anterior...)
    datos = st.session_state.alumno_datos
    st.success(f"🎓 **ALUMNO:** {datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}")
    
    res_f = {k: v for k, v in datos.items() if k.upper() not in ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']}
    entregas = sum(1 for v in res_f.values() if str(v).strip() not in ['0', '0.0', 'nan', '', 'False'])
    porc = int((entregas / len(res_f)) * 100) if len(res_f) > 0 else 0
    
    st.markdown(f'**Cumplimiento: {porc}%**')
    st.markdown(f'<div style="width:100%; background:#e0e0e0; border-radius:10px; height:18px;"><div style="width:{porc}%; background:#1D3557; height:18px; border-radius:10px;"></div></div>', unsafe_allow_html=True)
    
    df_res = pd.DataFrame(res_f.items(), columns=["Actividad", "Estado"])
    df_res["Estado"] = df_res["Estado"].apply(procesar_valor)
    filas = "".join([f'<tr><td style="border:1px solid #ddd; padding:8px;">{r["Actividad"]}</td><td style="border:1px solid #ddd; padding:8px;">{r["Estado"]}</td></tr>' for _, r in df_res.iterrows()])
    st.markdown(f'<div class="tabla-container"><table style="width:100%; border-collapse:collapse; color:black;"><tr style="background:#eee;"><th>Actividad</th><th>Estado</th></tr>{filas}</table></div>', unsafe_allow_html=True)
    
    if st.button("👥 OTRO ALUMNO"):
        st.session_state.pantalla = 'inicio'
        st.rerun()
