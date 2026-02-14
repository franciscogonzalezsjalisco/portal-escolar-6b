import streamlit as st
import pandas as pd
import time
from urllib.parse import quote
from fpdf import FPDF

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

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
    div.stButton > button {{
        width: 100% !important; height: 60px !important;
        border-radius: 12px !important; font-weight: 900 !important;
        color: white !important; text-transform: uppercase !important; border: none !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
    }}
    /* Estilo para el selectbox para que sea legible */
    .stSelectbox label {{ font-weight: bold !important; color: #1D3557 !important; }}
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

def generar_pdf(datos_alumno, semana, porcentaje, mensaje):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "PORTAL ESCOLAR 6 B - REPORTE SEMANAL", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Alumno: {datos_alumno.get('NOMBRE', '')} {datos_alumno.get('PATERNO', '')}", ln=True)
    pdf.cell(0, 10, f"Semana: {semana}", ln=True)
    pdf.cell(0, 10, f"Cumplimiento: {porcentaje}%", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(130, 10, " ACTIVIDAD", border=1)
    pdf.cell(60, 10, " ESTADO / CALIF.", border=1, ln=True)
    pdf.set_font("Helvetica", "", 10)
    omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    for k, v in datos_alumno.items():
        if k.upper() not in omitir:
            estado = procesar_valor(v).replace("❌ ", "").replace("✅ ", "")
            texto_k = str(k).encode('latin-1', 'ignore').decode('latin-1')
            pdf.cell(130, 8, f" {texto_k[:60]}", border=1)
            pdf.cell(60, 8, f" {estado}", border=1, ln=True)
    return bytes(pdf.output())

listado_hojas = obtener_nombres_hojas(SHEET_ID)

# --- PANTALLA 1: INICIO ---
if st.session_state.pantalla == 'inicio':
    st.title("🏫 Portal Escolar 6° B")
    st.markdown("### Selecciona la semana para comenzar:")
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
    
    if st.button("🔍 CONSULTAR REPORTE"):
        if mat_input:
            with st.spinner('Cargando datos...'):
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
    
    if st.button("⬅️ VOLVER AL INICIO"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

# --- PANTALLA 3: RESULTADOS (CON DESPLEGABLE) ---
elif st.session_state.pantalla == 'resultados':
    datos = st.session_state.alumno_datos
    omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    res_filtrado = {k: v for k, v in datos.items() if k.upper() not in omitir}
    
    # Cálculos
    total = len(res_filtrado)
    entregadas = sum(1 for v in res_filtrado.values() if str(v).strip() not in ['0', '0.0', 'nan', '', 'False'])
    porcentaje = int((entregadas / total) * 100) if total > 0 else 0
    color_p = "#E63946" if porcentaje < 50 else "#F4A261" if porcentaje < 80 else "#2A9D8F"
    
    st.success(f"🎓 **ALUMNO:** {datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}")
    
    # --- DESPLEGABLE DE NAVEGACIÓN RÁPIDA ---
    st.markdown("---")
    idx_actual = listado_hojas.index(st.session_state.semana_activa)
    nueva_semana = st.selectbox("📅 **Cambiar de semana:**", listado_hojas, index=idx_actual)
    
    if nueva_semana != st.session_state.semana_activa:
        st.session_state.semana_activa = nueva_semana
        # Buscar automáticamente los datos en la nueva semana
        df_nueva = cargar_datos(nueva_semana)
        df_nueva.columns = [str(col).strip() for col in df_nueva.columns]
        col_mat = [c for c in df_nueva.columns if "MATRICULA" in c.upper()]
        df_nueva['BUSCAR'] = df_nueva[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
        fila = df_nueva[df_nueva['BUSCAR'] == st.session_state.matricula_guardada.strip()]
        
        if not fila.empty:
            st.session_state.alumno_datos = fila.iloc[0].to_dict()
            st.rerun()
        else:
            st.warning(f"Matrícula no encontrada en {nueva_semana}")
    
    # Visualización de resultados
    st.markdown(f'**Progreso en {st.session_state.semana_activa}: {porcentaje}%**')
    st.markdown(f'<div style="width:100%; background:#e0e0e0; border-radius:10px; height:20px;"><div style="width:{porcentaje}%; background:{color_p}; height:20px; border-radius:10px;"></div></div>', unsafe_allow_html=True)
    
    df_res = pd.DataFrame(res_filtrado.items(), columns=["Actividad", "Estado"])
    df_res["Estado"] = df_res["Estado"].apply(procesar_valor)
    
    filas_tabla = "".join([f'<tr><td style="border:1px solid #ddd; padding:8px;">{row["Actividad"]}</td><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">{row["Estado"]}</td></tr>' for _, row in df_res.iterrows()])
    st.markdown(f'<div style="background: white; padding: 10px; border-radius: 10px; border: 1px solid #333;"><table style="width:100%; border-collapse: collapse; color: black;"><tr style="background: #eee;"><th>Actividad</th><th>Estado / Calif.</th></tr>{filas_tabla}</table></div>', unsafe_allow_html=True)

    # Botones inferiores
    col_a, col_b = st.columns(2)
    with col_a:
        pdf_data = generar_pdf(datos, st.session_state.semana_activa, porcentaje, "Reporte")
        st.download_button(label="📥 PDF", data=pdf_data, file_name=f"Reporte_{datos.get('PATERNO','')}.pdf", mime="application/pdf")
    with col_b:
        if st.button("🏠 INICIO"):
            st.session_state.pantalla = 'inicio'
            st.rerun()
