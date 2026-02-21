import streamlit as st
import pandas as pd
import time
from urllib.parse import quote
from fpdf import FPDF
from datetime import datetime
import pytz 
import requests

# 1. CONFIGURACIÓN E IDENTIDAD INSTITUCIONAL
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

NOMBRE_MAESTRO = "Profr. Francisco González"
URL_ESCUDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/ESCUDO%20690%20(1).png"
URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

# URL de tu Web App (Bitácora)
URL_LOG_SCRIPT = "https://script.google.com/macros/s/AKfycbz7fq8UUTz4JwoghvrzIZjVOFed4uWjq2_VYJIkL3HKHcE_izHMSRLQcrefrPf7pho/exec"

# MEMORIA DEL SISTEMA
if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'ID_USUARIO' not in st.session_state: st.session_state.ID_USUARIO = ""
if 'alumno_datos' not in st.session_state: st.session_state.alumno_datos = None

# 2. ESTILOS VISUALES (BLANCO Y AZUL MARINO - ANTI MODO OSCURO)
st.markdown(f"""
    <style>
    .stApp {{
        background-color: white !important;
        background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url("{URL_FONDO}") !important;
        background-size: cover !important;
    }}
    h1, h2, h3, h4, p, label, span, div, .stSelectbox p {{ color: #1D3557 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
    
    .banner-maestro {{
        text-align: center; background: #1D3557; color: white !important;
        padding: 15px; border-radius: 12px; margin-bottom: 20px; font-weight: bold;
    }}
    
    /* Botones Blancos con letras Azul Marino */
    div.stButton > button {{
        background-color: white !important; color: #1D3557 !important;
        border: 2px solid #1D3557 !important; width: 100% !important; height: 50px !important;
        border-radius: 12px !important; font-weight: 900 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }}
    
    .tabla-container {{
        background: white; padding: 15px; border-radius: 15px; 
        border: 2px solid #1D3557; margin-top: 15px;
    }}
    </style>
    """, unsafe_allow_html=True)

st.markdown(f'<div class="banner-maestro">🏫 {NOMBRE_MAESTRO} <br> <span style="color:white; font-size: 0.8rem;">6° B - Control Escolar Digital</span></div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 0.6, 1])
with c2: st.image(URL_ESCUDO, use_container_width=True)

# 3. FUNCIONES LÓGICAS
def registrar_en_bitacora(matricula, nombre, semana, accion):
    try:
        payload = {
            "fecha": datetime.now(pytz.timezone('America/Mexico_City')).strftime("%d/%m/%Y %H:%M:%S"),
            "matricula": str(matricula),
            "nombre": str(nombre),
            "semana": str(semana),
            "accion": str(accion)
        }
        requests.post(URL_LOG_SCRIPT, json=payload, timeout=5)
    except: pass

def procesar_valor(val):
    v_str = str(val).strip().upper()
    if v_str in ['NAN', '', '0', '0.0', 'FALSE', 'FALSO']: return "❌ Pendiente"
    if v_str in ['1', '1.0', 'TRUE', 'VERDADERO']: return "✅ Completado"
    return str(val)

@st.cache_data(ttl=60)
def obtener_nombres_hojas(sid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=xlsx"
        xls = pd.ExcelFile(url, engine='openpyxl')
        return xls.sheet_names
    except: return ["Semana 1"]

@st.cache_data(ttl=0) 
def cargar_datos(nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={int(time.time())}"
    return pd.read_csv(url)

def generar_pdf(datos, semana, porcentaje):
    pdf = FPDF()
    pdf.add_page()
    nombre_full = f"{datos.get('NOMBRE', '')} {datos.get('PATERNO', '')} {datos.get('MATERNO', '')}".strip()
    
    # Encabezado
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(29, 53, 87)
    pdf.cell(0, 10, f"REPORTE ESCOLAR PERSONALIZADO", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"ALUMNO: {nombre_full}", ln=True, align="C")
    pdf.ln(5)
    
    # Detalles técnicos
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, f"Responsable: {NOMBRE_MAESTRO}", ln=True)
    pdf.cell(0, 7, f"Semana Consultada: {semana}", ln=True)
    pdf.cell(0, 7, f"Cumplimiento Semanal: {porcentaje}%", ln=True)
    pdf.ln(5)
    
    # Tabla
    pdf.set_fill_color(29, 53, 87)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(130, 8, " ACTIVIDAD", border=1, fill=True)
    pdf.cell(60, 8, " ESTADO", border=1, fill=True, ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    for k, v in datos.items():
        if k.upper() not in omitir:
            res = procesar_valor(v).replace("❌ ", "").replace("✅ ", "")
            pdf.cell(130, 7, f" {str(k)[:65]}", border=1)
            pdf.cell(60, 7, f" {res}", border=1, ln=True)
    
    # SUSTENTO DE DESCARGA
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    timestamp = datetime.now(pytz.timezone('America/Mexico_City')).strftime("%d/%m/%Y a las %H:%M:%S")
    pdf.multi_cell(0, 5, f"Evidencia de consulta digital generada para el alumno {nombre_full}.\nMatrícula: {datos.get('MATRICULA','')}\nFecha y hora oficial de descarga: {timestamp} hrs.\nEste documento sirve como comprobante de seguimiento para padres de familia.", align='C')
    
    return bytes(pdf.output())

listado_hojas = obtener_nombres_hojas(SHEET_ID)

# --- FLUJO DE PANTALLAS ---

if st.session_state.pantalla == 'inicio':
    st.markdown("<h4 style='text-align: center;'>Selecciona la semana de consulta</h4>", unsafe_allow_html=True)
    for i in range(0, len(listado_hojas), 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < len(listado_hojas):
                nombre_h = listado_hojas[idx]
                with cols[j]:
                    if st.button(nombre_h, key=f"btn_{idx}"):
                        st.session_state.semana_activa = nombre_h
                        st.session_state.pantalla = 'matricula'
                        st.rerun()

elif st.session_state.pantalla == 'matricula':
    st.markdown(f"<h4 style='text-align: center;'>📍 Semana: {st.session_state.semana_activa}</h4>", unsafe_allow_html=True)
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
                    nom_completo = f"{st.session_state.alumno_datos.get('NOMBRE','')} {st.session_state.alumno_datos.get('PATERNO','')}"
                    registrar_en_bitacora(st.session_state.ID_USUARIO, nom_completo, st.session_state.semana_activa, "Ingreso")
                    st.session_state.pantalla = 'resultados'
                    st.rerun()
                else: st.error("❌ Matrícula no encontrada.")
    if st.button("⬅️ VOLVER AL MENÚ"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

elif st.session_state.pantalla == 'resultados':
    datos = st.session_state.alumno_datos
    nombre_completo = f"{datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}"
    st.success(f"🎓 **ALUMNO:** {nombre_completo}")
    
    # NAVEGACIÓN RÁPIDA (Menu Desplegable)
    idx_s = listado_hojas.index(st.session_state.semana_activa)
    nueva_s = st.selectbox("📅 **Cambiar semana de consulta:**", listado_hojas, index=idx_s)
    
    if nueva_s != st.session_state.semana_activa:
        st.session_state.semana_activa = nueva_s
        df_n = cargar_datos(nueva_s)
        df_n.columns = [str(col).strip() for col in df_n.columns]
        col_m = [c for c in df_n.columns if "MATRICULA" in c.upper()]
        df_n['BUSCAR'] = df_n[col_m[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
        fila = df_n[df_n['BUSCAR'] == st.session_state.ID_USUARIO]
        if not fila.empty:
            st.session_state.alumno_datos = fila.iloc[0].to_dict()
            registrar_en_bitacora(st.session_state.ID_USUARIO, nombre_completo, nueva_s, "Cambio Semana")
            st.rerun()

    # Cálculo de Progreso
    res_f = {k: v for k, v in datos.items() if k.upper() not in ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']}
    entregas = sum(1 for v in res_f.values() if str(v).strip() not in ['0', '0.0', 'nan', '', 'False'])
    porc = int((entregas / len(res_f)) * 100) if len(res_f) > 0 else 0
    
    st.markdown(f'**Nivel de cumplimiento: {porc}%**')
    st.markdown(f'<div style="width:100%; background:#e0e0e0; border-radius:10px; height:18px;"><div style="width:{porc}%; background:#1D3557; height:18px; border-radius:10px;"></div></div>', unsafe_allow_html=True)
    
    # Tabla
    df_res = pd.DataFrame(res_f.items(), columns=["Actividad", "Estado"])
    df_res["Estado"] = df_res["Estado"].apply(procesar_valor)
    filas = "".join([f'<tr><td style="border:1px solid #ddd; padding:8px;">{r["Actividad"]}</td><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">{r["Estado"]}</td></tr>' for _, r in df_res.iterrows()])
    st.markdown(f'<div class="tabla-container"><table style="width:100%; border-collapse:collapse; color:black;"><tr style="background:#eee;"><th>Actividad</th><th>Estado / Calif.</th></tr>{filas}</table></div>', unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        pdf_b = generar_pdf(datos, st.session_state.semana_activa, porc)
        if st.download_button(f"📥 PDF DE {datos.get('PATERNO','')}", data=pdf_b, file_name=f"Reporte_{datos.get('PATERNO','')}.pdf", mime="application/pdf"):
             registrar_en_bitacora(st.session_state.ID_USUARIO, nombre_completo, st.session_state.semana_activa, "Descarga PDF")
    with c2:
        if st.button("👥 OTRO ALUMNO"):
            st.session_state.pantalla = 'inicio'
            st.rerun()
