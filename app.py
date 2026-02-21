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
if 'usuario' not in st.session_state: st.session_state.usuario = None

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
    </style>
    """, unsafe_allow_html=True)
    /* Estilo para la firma en el pie de página */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.8); /* Fondo semi-transparente */
        color: #1D3557;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        font-weight: bold;
        border-top: 1px solid #1D3557;
        z-index: 100;
    }

# 3. --- ENCABEZADO PRINCIPAL (LOGO Y TÍTULO) ---
col1, col2, col3 = st.columns([1, 2, 1])
st.markdown("<h2 style='text-align: center;'>URBANA 690</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #457B9D !important;'>6° Grado Grupo B</h4>", unsafe_allow_html=True)
st.markdown("---")
    
# 3. FUNCIONES
def registrar_en_bitacora(matricula, nombre, semana, accion):
    """Envío definitivo con simulación de navegador para evitar bloqueos de Google"""
    try:
        ts = datetime.now(pytz.timezone('America/Mexico_City')).strftime("%d/%m/%Y %H:%M:%S")
        params = {
            "fecha": ts,
            "matricula": str(matricula),
            "nombre": str(nombre),
            "semana": str(semana),
            "accion": str(accion)
        }
        # Engañamos a Google para que crea que somos un navegador real
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Enviamos vía GET
        requests.get(URL_LOG_SCRIPT, params=params, headers=headers, timeout=10)
        st.toast(f"Registro exitoso: {accion}", icon="✅")
    except:
        pass
        
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
    
    st.markdown("---") #
    with st.expander("🔐 Acceso Maestro"):
        pw = st.text_input("Contraseña:", type="password")
        if pw == PASS_MAESTRO:
            sem_m = st.selectbox("Semana para reporte grupal:", listado_hojas)
        if st.button("🚀 GENERAR PDF GRUPAL"):
                with st.spinner("Generando todas las hojas..."):
                    df_m = cargar_datos(sem_m)
                    pdf_m = FPDF()
                    for _, f in df_m.iterrows(): 
                        crear_hoja_alumno_pdf(pdf_m, f.to_dict(), sem_m, es_grupal=True)
                    
                    # MÉTODO COMPATIBLE CON TODAS LAS VERSIONES DE FPDF2
                    try:
                        # Obtenemos los bytes directamente
                        pdf_bytes = bytes(pdf_m.output()) 
                    except:
                        # Si falla lo anterior, usamos el método alternativo
                        pdf_bytes = pdf_m.output(dest='S').encode('latin-1') if hasattr(pdf_m, 'output') else b""

                    if pdf_bytes:
                        st.download_button(
                            label=f"📥 Descargar {sem_m}", 
                            data=pdf_bytes, 
                            file_name=f"Grupo_6B_{sem_m}.pdf",
                            mime="application/pdf"
                        )
                        # REGISTRO DEL MAESTRO
                        registrar_en_bitacora("MAESTRO", NOMBRE_MAESTRO, sem_m, "Descarga Masiva")
                    else:
                        st.error("No se pudo generar el archivo PDF.")
                    
elif st.session_state.pantalla == 'matricula':
    st.markdown(f"<h4 style='text-align: center;'>📍 {st.session_state.semana_activa}</h4>", unsafe_allow_html=True)
    mat_in = st.text_input("Matrícula:", value=st.session_state.ID_USUARIO)
    if st.button("🔍 VER REPORTE"):
        if mat_in:
            st.session_state.ID_USUARIO = mat_in.strip()
            df = cargar_datos(st.session_state.semana_activa)
            df.columns = [str(c).strip() for c in df.columns]
            col_m = [c for c in df.columns if "MATRICULA" in c.upper()]
            if col_m:
                df['BUSCAR'] = df[col_m[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
                fila = df[df['BUSCAR'] == st.session_state.ID_USUARIO]
                if not fila.empty:
                    st.session_state.alumno_datos = fila.iloc[0].to_dict()
                    registrar_en_bitacora(st.session_state.ID_USUARIO, st.session_state.alumno_datos.get('NOMBRE',''), st.session_state.semana_activa, "Ingreso")
                    st.session_state.pantalla = 'resultados'; st.rerun()
                else: st.error("❌ No encontrada")
    if st.button("⬅️ VOLVER"): st.session_state.pantalla = 'inicio'; st.rerun()

elif st.session_state.pantalla == 'resultados':
    datos = st.session_state.alumno_datos
    nombre_c = f"{datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}"
    st.success(f"🎓 **ALUMNO:** {nombre_c}")
    
    # REINTEGRACIÓN: NAVEGACIÓN ENTRE SEMANAS
    idx_s = listado_hojas.index(st.session_state.semana_activa)
    nueva_s = st.selectbox("📅 **Ver otra semana:**", listado_hojas, index=idx_s)
    if nueva_s != st.session_state.semana_activa:
        st.session_state.semana_activa = nueva_s
        df_n = cargar_datos(nueva_s)
        df_n.columns = [str(c).strip() for c in df_n.columns]
        col_m = [c for c in df_n.columns if "MATRICULA" in c.upper()]
        df_n['BUSCAR'] = df_n[col_m[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
        fila = df_n[df_n['BUSCAR'] == st.session_state.ID_USUARIO]
        if not fila.empty:
            st.session_state.alumno_datos = fila.iloc[0].to_dict()
            registrar_en_bitacora(st.session_state.ID_USUARIO, nombre_c, nueva_s, "Cambio Semana")
            st.rerun()

    res_f = {k: v for k, v in datos.items() if k.upper() not in ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']}
    entregas = sum(1 for v in res_f.values() if str(v).strip() not in ['0', '0.0', 'nan', '', 'False'])
    porc = int((entregas / len(res_f)) * 100) if len(res_f) > 0 else 0
    st.markdown(f'**Cumplimiento: {porc}%**')
    st.markdown(f'<div style="width:100%; background:#e0e0e0; border-radius:10px; height:18px;"><div style="width:{porc}%; background:#1D3557; height:18px; border-radius:10px;"></div></div>', unsafe_allow_html=True)
    
    df_res = pd.DataFrame(res_f.items(), columns=["Actividad", "Estado"])
    df_res["Estado"] = df_res["Estado"].apply(procesar_valor)
    filas = "".join([f'<tr><td style="border:1px solid #ddd; padding:8px;">{r["Actividad"]}</td><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">{r["Estado"]}</td></tr>' for _, r in df_res.iterrows()])
    st.markdown(f'<div class="tabla-container"><table style="width:100%; border-collapse:collapse; color:black;"><tr style="background:#eee;"><th>Actividad</th><th>Estado</th></tr>{filas}</table></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        pdf_ind = FPDF()
        crear_hoja_alumno_pdf(pdf_ind, datos, st.session_state.semana_activa)
        if st.download_button(f"📥 PDF", data=bytes(pdf_ind.output()), file_name=f"Reporte_{datos.get('PATERNO','')}.pdf"):
            registrar_en_bitacora(st.session_state.ID_USUARIO, nombre_c, st.session_state.semana_activa, "Descarga PDF")
    with c2:
        if st.button("👥 OTRO ALUMNO"): st.session_state.pantalla = 'inicio'; st.rerun()

        # Firma fija en la parte inferior
st.markdown(f'<div class="footer">{NOMBRE_MAESTRO}</div>', unsafe_allow_html=True)
