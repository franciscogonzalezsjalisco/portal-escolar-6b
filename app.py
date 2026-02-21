import streamlit as st
import pandas as pd
import time
from urllib.parse import quote
from fpdf import FPDF

# 1. CONFIGURACIÓN E IDENTIDAD INSTITUCIONAL
st.set_page_config(page_title="Portal Escolar 6°B U.690", layout="centered")

# --- VARIABLES DE PERSONALIZACIÓN ---
NOMBRE_MAESTRO = "Profr. Francisco González"
URL_ESCUDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/ESCUDO%20690%20(1).png"
URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

# --- MEMORIA DEL SISTEMA ---
if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'ID_USUARIO' not in st.session_state: st.session_state.ID_USUARIO = ""
if 'alumno_datos' not in st.session_state: st.session_state.alumno_datos = None

# 2. ESTILOS VISUALES (FORZADO ANTI MODO OSCURO)
st.markdown(f"""
    <style>
    /* Fondo General */
    .stApp {{
        background-color: white !important;
        background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url("{URL_FONDO}") !important;
        background-size: cover !important;
    }}

    /* Forzar color de texto global a Azul Marino/Negro */
    h1, h2, h3, h4, p, label, span, div, .stSelectbox p {{ 
        color: #1D3557 !important; 
    }}

    /* Banner del Maestro */
    .banner-maestro {{
        text-align: center;
        background: #1D3557;
        color: white !important;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
        font-weight: bold;
    }}
    .banner-maestro span {{ color: white !important; }}

    /* BOTONES DE SEMANAS (Fondo Blanco, Letras Azul Marino) */
    div.stButton > button {{
        background-color: white !important;
        color: #1D3557 !important;
        border: 2px solid #1D3557 !important;
        width: 100% !important;
        height: 60px !important;
        border-radius: 12px !important;
        font-weight: 900 !important;
        font-size: 16px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        transition: 0.3s;
    }}
    
    /* Efecto al pasar el mouse por los botones */
    div.stButton > button:hover {{
        background-color: #f0f4f8 !important;
        border-color: #457B9D !important;
    }}

    /* Estilo de la tabla de resultados */
    .tabla-container {{
        background: white; padding: 15px; border-radius: 15px; 
        border: 2px solid #1D3557; margin-top: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }}
    
    /* Input de matrícula */
    .stTextInput input {{
        background-color: white !important;
        color: black !important;
        border: 1px solid #1D3557 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# Encabezado Institucional
st.markdown(f'<div class="banner-maestro">🏫 {NOMBRE_MAESTRO} <br> <span style="font-size: 0.9rem;">Portal de Seguimiento - 6° B</span></div>', unsafe_allow_html=True)

# Escudo
c1, c2, c3 = st.columns([1, 0.6, 1])
with c2:
    st.image(URL_ESCUDO, use_container_width=True)

# 3. FUNCIONES TÉCNICAS
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
    pdf.cell(0, 10, f"REPORTE ESCOLAR - {NOMBRE_MAESTRO}", ln=True, align="C")
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

# --- FLUJO DE PANTALLAS ---

if st.session_state.pantalla == 'inicio':
    st.markdown("<h3 style='text-align: center;'>Selecciona la semana de consulta</h3>", unsafe_allow_html=True)
    
    # Grid de botones (Ahora todos Blancos con borde Azul)
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
    
    # Botón de consulta (Mismo estilo para consistencia)
    if st.button("🔍 CONSULTAR REPORTE"):
        if mat_input:
            st.session_state.ID_USUARIO = mat_input.strip()
            with st.spinner('Buscando registros...'):
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
                    else: st.error("❌ No se encontró la matrícula.")

    if st.button("⬅️ VOLVER AL LISTADO"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

elif st.session_state.pantalla == 'resultados':
    datos = st.session_state.alumno_datos
    st.markdown(f"#### 🎓 Alumno: {datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}")
    
    # Navegador rápido
    idx_s = listado_hojas.index(st.session_state.semana_activa)
    nueva_s = st.selectbox("📅 **Ver otra semana:**", listado_hojas, index=idx_s)
    
    if nueva_s != st.session_state.semana_activa:
        st.session_state.semana_activa = nueva_s
        df_n = cargar_datos(nueva_s)
        df_n.columns = [str(col).strip() for col in df_n.columns]
        col_m = [c for c in df_n.columns if "MATRICULA" in c.upper()]
        df_n['BUSCAR'] = df_n[col_m[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
        fila = df_n[df_n['BUSCAR'] == st.session_state.ID_USUARIO]
        if not fila.empty:
            st.session_state.alumno_datos = fila.iloc[0].to_dict()
            st.rerun()

    # Tabla y Progreso
    res_f = {k: v for k, v in datos.items() if k.upper() not in ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']}
    entregas = sum(1 for v in res_f.values() if str(v).strip() not in ['0', '0.0', 'nan', '', 'False'])
    porc = int((entregas / len(res_f)) * 100) if len(res_f) > 0 else 0
    color_p = "#1D3557" # Azul Marino para la barra

    st.markdown(f'**Cumplimiento: {porc}%**')
    st.markdown(f'<div style="width:100%; background:#e0e0e0; border-radius:10px; height:18px;"><div style="width:{porc}%; background:{color_p}; height:18px; border-radius:10px;"></div></div>', unsafe_allow_html=True)
    
    df_res = pd.DataFrame(res_f.items(), columns=["Actividad", "Estado"])
    df_res["Estado"] = df_res["Estado"].apply(procesar_valor)
    filas = "".join([f'<tr><td style="border:1px solid #ddd; padding:8px;">{r["Actividad"]}</td><td style="border:1px solid #ddd; padding:8px; font-weight:bold;">{r["Estado"]}</td></tr>' for _, r in df_res.iterrows()])
    st.markdown(f'<div class="tabla-container"><table style="width:100%; border-collapse:collapse; color:black;"><tr style="background:#eee;"><th>Actividad</th><th>Estado</th></tr>{filas}</table></div>', unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        pdf_b = generar_pdf(datos, st.session_state.semana_activa, porc)
        st.download_button("📥 DESCARGAR PDF", data=pdf_b, file_name=f"Reporte_{datos.get('PATERNO','')}.pdf", mime="application/pdf")
    with c2:
        if st.button("👥 OTRO ALUMNO"):
            st.session_state.pantalla = 'inicio'
            st.rerun()
