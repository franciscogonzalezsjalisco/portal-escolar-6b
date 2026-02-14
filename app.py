import streamlit as st
import pandas as pd
import time
from urllib.parse import quote
from fpdf import FPDF
import io

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

# --- INICIALIZAR MEMORIA ---
if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'matricula_guardada' not in st.session_state: st.session_state.matricula_guardada = ""
if 'alumno_datos' not in st.session_state: st.session_state.alumno_datos = None

URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

# 2. CSS ANTI MODO-OSCURO Y ESTÉTICA
st.markdown(f"""
    <style>
    .stApp {{
        background: white !important;
        background: linear-gradient(rgba(255,255,255,0.7), rgba(255,255,255,0.7)), url("{URL_FONDO}") !important;
        background-size: cover !important;
        background-attachment: fixed !important;
    }}
    h1, h2, h3, p, label, span, div {{ color: black !important; -webkit-text-fill-color: black !important; }}
    
    div.stButton > button {{
        width: 100% !important; height: 70px !important;
        border-radius: 15px !important; font-weight: 900 !important;
        font-size: 18px !important; color: white !important;
        -webkit-text-fill-color: white !important;
        text-transform: uppercase !important; border: none !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
    }}
    input {{ background-color: #f0f2f6 !important; color: black !important; border: 2px solid #1D3557 !important; }}
    </style>
    """, unsafe_allow_html=True)

# 3. FUNCIONES DE DATOS Y PDF
@st.cache_data(ttl=60)
def obtener_nombres_hojas(sid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=xlsx"
        xls = pd.ExcelFile(url, engine='openpyxl')
        return xls.sheet_names
    except: return ["S1 Enero"]

@st.cache_data(ttl=0) 
def cargar_datos(nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={int(time.time())}"
    return pd.read_csv(url)

def generar_pdf(datos_alumno, semana, porcentaje, mensaje):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "PORTAL ESCOLAR 6° B - REPORTE SEMANAL", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Alumno: {datos_alumno.get('NOMBRE', '')} {datos_alumno.get('PATERNO', '')}", ln=True)
    pdf.cell(0, 10, f"Semana: {semana}", ln=True)
    pdf.cell(0, 10, f"Cumplimiento: {porcentaje}%", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(140, 10, " ACTIVIDAD", border=1)
    pdf.cell(50, 10, " ESTADO", border=1, ln=True)
    pdf.set_font("Arial", "", 10)
    omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    for k, v in datos_alumno.items():
        if k.upper() not in omitir:
            estado = "Completado" if str(v).upper().strip() in ['1', '1.0', 'TRUE'] else "Pendiente"
            pdf.cell(140, 8, f" {str(k)[:60]}", border=1)
            pdf.cell(50, 8, f" {estado}", border=1, ln=True)
    return pdf.output()

listado_hojas = obtener_nombres_hojas(SHEET_ID)

# --- PANTALLA 1: INICIO ---
if st.session_state.pantalla == 'inicio':
    st.title("🏫 Portal Escolar 6° B")
    st.markdown("### Selecciona la semana:")
    colores = ["#E63946", "#457B9D", "#2A9D8F", "#F4A261", "#8338EC"]
    for i in range(0, len(listado_hojas), 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < len(listado_hojas):
                nombre_h = listado_hojas[idx]
                with cols[j]:
                    st.markdown(f'<style>button[key="btn_{idx}"] {{ background-color: {colores[idx % 5]} !important; }}</style>', unsafe_allow_html=True)
                    if st.button(nombre_h, key=f"btn_{idx}"):
                        st.session_state.semana_activa = nombre_h
                        st.session_state.pantalla = 'matricula'
                        st.rerun()

# --- PANTALLA 2: MATRÍCULA ---
elif st.session_state.pantalla == 'matricula':
    st.title(f"📍 {st.session_state.semana_activa}")
    mat_input = st.text_input("Ingresa la matrícula del alumno:", value=st.session_state.matricula_guardada)
    st.session_state.matricula_guardada = mat_input
    if st.button("🔍 CONSULTAR AHORA"):
        if mat_input:
            df = cargar_datos(st.session_state.semana_activa)
            df.columns = [str(col).strip() for col in df.columns]
            col_mat = [c for c in df.columns if "MATRICULA" in c.upper()]
            if col_mat:
                df['BUSCAR'] = df[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
                fila = df[df['BUSCAR'] == mat_input.strip()]
                if not fila.empty:
                    st.session_state.alumno_datos = fila.iloc[0].to_dict()
                    st.session_state.pantalla = 'resultados'
                    st.rerun()
                else: st.error("❌ Matrícula no encontrada.")
    if st.button("⬅️ VOLVER AL MENÚ"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

# --- PANTALLA 3: RESULTADOS ---
elif st.session_state.pantalla == 'resultados':
    datos = st.session_state.alumno_datos
    # Ocultar Materno y filtrar columnas
    omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    res_filtrado = {k: v for k, v in datos.items() if k.upper() not in omitir}
    
    # Cálculos
    total = len(res_filtrado)
    entregadas = sum(1 for v in res_filtrado.values() if str(v).upper().strip() in ['1', '1.0', 'TRUE'])
    porcentaje = int((entregadas / total) * 100) if total > 0 else 0
    
    color_p = "#E63946" if porcentaje < 50 else "#F4A261" if porcentaje < 80 else "#2A9D8F"
    mensaje = "🌟 ¡Excelente trabajo!" if porcentaje == 100 else "✅ ¡Muy bien!" if porcentaje >= 80 else "⚠️ Tienes pendientes." if porcentaje >= 50 else "🚩 ¡Atención requerida!"

    st.success(f"🎓 **ALUMNO:** {datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}")
    
    # Barra de progreso
    st.markdown(f'**Progreso: {porcentaje}%**')
    st.markdown(f'<div style="width:100%; background:#e0e0e0; border-radius:10px;"><div style="width:{porcentaje}%; background:{color_p}; height:20px; border-radius:10px;"></div></div>', unsafe_allow_
