import streamlit as st
import pandas as pd
import time
from urllib.parse import quote
from fpdf import FPDF

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

# --- MEMORIA DEL SISTEMA ---
if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'matricula_guardada' not in st.session_state: st.session_state.matricula_guardada = ""
if 'alumno_datos' not in st.session_state: st.session_state.alumno_datos = None

URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

st.markdown(f"""
    <style>
    .stApp {{
        background: white !important;
        background: linear-gradient(rgba(255,255,255,0.7), rgba(255,255,255,0.7)), url("{URL_FONDO}") !important;
        background-size: cover !important;
        background-attachment: fixed !important;
    }}
    h1, h2, h3, p, label, span, div {{ color: black !important; -webkit-text-fill-color: black !important; }}
    
    /* Botones vibrantes */
    div.stButton > button {{
        width: 100% !important; height: 55px !important;
        border-radius: 12px !important; font-weight: 900 !important;
        color: white !important; text-transform: uppercase !important; border: none !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
    }}
    
    /* Contenedor de tabla */
    .tabla-container {{
        background: white; padding: 15px; border-radius: 15px; 
        border: 2px solid #1D3557; margin-top: 15px;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. FUNCIONES DE LÓGICA
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
    except: return ["S1 Enero"]

@st.cache_data(ttl=0) 
def cargar_datos(nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={int(time.time())}"
    return pd.read_csv(url)

def generar_pdf(datos_alumno, semana, porcentaje):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "REPORTE ESCOLAR - 6 B", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Alumno: {datos_alumno.get('NOMBRE', '')} {datos_alumno.get('PATERNO', '')}", ln=True)
    pdf.cell(0, 10, f"Semana: {semana} | Cumplimiento: {porcentaje}%", ln=True)
    pdf.ln(5)
    omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(130, 8, " ACTIVIDAD", border=1)
    pdf.cell(60, 8, " ESTADO", border=1, ln=True)
    pdf.set_font("Helvetica", "", 10)
    for k, v in datos_alumno.items():
        if k.upper() not in omitir:
            res = procesar_valor(v).replace("❌ ", "").replace("✅ ", "")
            pdf.cell(130, 7, f" {str(k)[:60]}", border=1)
            pdf.cell(60, 7, f" {res}", border=1, ln=True)
    return bytes(pdf.output())

listado_hojas = obtener_nombres_hojas(SHEET_ID)

# --- PANTALLA 1: INICIO (SELECCIÓN INICIAL) ---
if st.session_state.pantalla == 'inicio':
    st.title("🏫 Portal Escolar 6° B")
    st.markdown("### Selecciona la semana para empezar:")
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

# --- PANTALLA 2: CAPTURA DE MATRÍCULA ---
elif st.session_state.pantalla == 'matricula':
    st.title(f"📍 {st.session_state.semana_activa}")
    mat_input = st.text_input("Ingresa la matrícula del alumno:", value=st.session_state.matricula_guardada)
    
    if st.button("🔍 VER REPORTE"):
        if mat_input:
            st.session_state.matricula_guardada = mat_input.strip()
            df = cargar_datos(st.session_state.semana_activa)
            df.columns = [str(col).strip() for col in df.columns]
            col_mat = [c for c in df.columns if "MATRICULA" in c.upper()]
            if col_mat:
                df['BUSCAR'] = df[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
                fila = df[df['BUSCAR'] == st.session_state.matricula_guardada]
                if not fila.empty:
                    st.session_state.alumno_datos = fila.iloc[0].to_dict()
                    st.session_state.pantalla = 'resultados'
                    st.rerun()
                else: st.error("❌ No encontramos esa matrícula en esta semana.")

# --- PANTALLA 3: RESULTADOS (CON NAVEGACIÓN RÁPIDA) ---
elif st.session_state.pantalla == 'resultados':
    # Encabezado con Nombre
    st.subheader(f"👤 {st.session_state.alumno_datos.get('NOMBRE', '')} {st.session_state.alumno_datos.get('PATERNO', '')}")
    
    # --- MENÚ DESPLEGABLE DE SEMANAS (Sustituye a volver a inicio) ---
    st.markdown("#### 📅 Cambiar de semana:")
    idx_s = listado_hojas.index(st.session_state.semana_activa)
    nueva_s = st.selectbox("Selecciona otra semana para ver los resultados del mismo alumno:", listado_hojas, index=idx_s, label_visibility="collapsed")
    
    # Si el usuario cambia la semana en el desplegable
    if nueva_s != st.session_state.semana_activa:
        st.session_state.semana_activa = nueva_s
        with st.spinner('Actualizando reporte...'):
            df_n = cargar_datos(nueva_s)
            df_n.columns = [str(col).strip() for col in df_n.columns]
            col_m = [c for c in df_n.columns if "MATRICULA" in c.upper()]
            df_n['BUSCAR'] = df_n[col_m[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
            fila = df_n[df_n['BUSCAR'] == st.session_state.matricula_guardada]
            if not fila.empty:
                st.session_state.alumno_datos = fila.iloc[0].to_dict()
                st.rerun()
            else:
                st.warning(f"La matrícula {st.session_state.matricula_guardada} no tiene registros en la {nueva_s}.")

    # Datos actuales
    datos = st.session_state.alumno_datos
    omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    res_f = {k: v for k, v in datos.items() if k.upper() not in omitir}
    
    # Barra de Progreso
    total = len(res_f)
    entregas = sum(1 for v in res_f.values() if str(v).strip() not in ['0', '0.0', 'nan', '', 'False'])
    porc = int((entregas / total) * 100) if total > 0 else 0
    color_p = "#E63946" if porc < 50 else "#F4A261" if porc < 80 else "#2A9D8F"

    st.markdown(f'**Progreso: {porc}%**')
    st.markdown(f'<div style="width:100%; background:#e0e0e0; border-radius:10px; height:18px;"><div style="width:{porc}%; background:{color_p}; height:18px; border-radius:10px;"></div></div>', unsafe_allow_html=True)
    
    # Tabla de Resultados
    df_res = pd.DataFrame(res_f.items(), columns=["Actividad", "Estado"])
    df_res["Estado"] = df_res["Estado"].apply(procesar_valor)
    
    filas = "".join([f'<tr><td style="border:1px solid #ddd; padding:8px;">{r["Actividad"]}</td><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">{r["Estado"]}</td></tr>' for _, r in df_res.iterrows()])
    st.markdown(f'<div class="tabla-container"><table style="width:100%; border-collapse:collapse; color:black;"><tr style="background:#eee;"><th>Actividad</th><th>Estado</th></tr>{filas}</table></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # Botones de Acción
    c1, c2 = st.columns(2)
    with c1:
        pdf_b = generar_pdf(datos, st.session_state.semana_activa, porc)
        st.download_button("📥 DESCARGAR PDF", data=pdf_b, file_name=f"Reporte_{datos.get('PATERNO','')}_{st.session_state.semana_activa}.pdf", mime="application/pdf")
    with c2:
        if st.button("🔄 CAMBIAR MATRÍCULA"):
            st.session_state.pantalla = 'inicio'
            st.session_state.matricula_guardada = "" # Borramos solo si quieren cambiar de usuario
            st.rerun()
