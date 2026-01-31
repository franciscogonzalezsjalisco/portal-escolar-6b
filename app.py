import streamlit as st
import pandas as pd
import time
from urllib.parse import quote

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Seguimiento 6°B", layout="centered")

# --- INICIALIZAR MEMORIA ---
if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'matricula_guardada' not in st.session_state: st.session_state.matricula_guardada = ""
if 'alumno_datos' not in st.session_state: st.session_state.alumno_datos = None

URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

# 2. CSS INTEGRADO (ANTI MODO-OSCURO + BOTONES HOMOGÉNEOS)
st.markdown(f"""
    <style>
    .stApp {{
        background: white !important;
        background: linear-gradient(rgba(255,255,255,0.7), rgba(255,255,255,0.7)), url("{URL_FONDO}") !important;
        background-size: cover !important;
        background-attachment: fixed !important;
    }}
    h1, h2, h3, p, label, span, div {{
        color: black !important;
        -webkit-text-fill-color: black !important;
    }}
    div.stButton > button {{
        width: 100% !important;
        height: 80px !important;
        border-radius: 15px !important;
        font-weight: 900 !important;
        font-size: 18px !important;
        color: white !important;
        -webkit-text-fill-color: white !important;
        text-transform: uppercase !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
        border: none !important;
    }}
    /* Input más visible */
    input {{
        background-color: #f0f2f6 !important;
        color: black !important;
        border: 2px solid #1D3557 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. FUNCIONES DE DATOS
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

listado_hojas = obtener_nombres_hojas(SHEET_ID)

# --- PANTALLA 1: SELECCIÓN DE SEMANA ---
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
                color_v = colores[idx % len(colores)]
                with cols[j]:
                    st.markdown(f'<style>button[key="btn_{idx}"] {{ background-color: {color_v} !important; }}</style>', unsafe_allow_html=True)
                    if st.button(nombre_h, key=f"btn_{idx}"):
                        st.session_state.semana_activa = nombre_h
                        st.session_state.pantalla = 'matricula'
                        st.rerun()

# --- PANTALLA 2: CAPTURA DE MATRÍCULA ---
elif st.session_state.pantalla == 'matricula':
    st.title(f"📍 {st.session_state.semana_activa}")
    
    mat_input = st.text_input("Ingresa la matrícula del alumno:", value=st.session_state.matricula_guardada)
    st.session_state.matricula_guardada = mat_input

    # Botones de acción
    if st.button("🔍 CONSULTAR AHORA"):
        if mat_input.strip() == "":
            st.warning("⚠️ Por favor, escribe una matrícula.")
        else:
            with st.spinner('Buscando datos...'):
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
                    else:
                        st.error("❌ Matrícula no encontrada.")

    if st.button("⬅️ VOLVER AL MENÚ"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

# --- PANTALLA 3: RESULTADOS ---
elif st.session_state.pantalla == 'resultados':
    datos = st.session_state.alumno_datos
    st.title("📑 Reporte de Actividades")
    st.success(f"🎓 **ALUMNO:** {datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}")
    
    # Procesar tabla
    omitir = ['NOMBRE', 'PATERNO', 'MATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    res_filtrado = {k: v for k, v in datos.items() if k.upper() not in omitir}
    df_res = pd.DataFrame(res_filtrado.items(), columns=["Actividad", "Estado"])
    
    def limpiar(val):
        v = str(val).upper().strip()
        if v in ['1', '1.0', 'TRUE']: return "✅ Completado"
        if v in ['0', '0.0', 'FALSE', 'NAN', '']: return "❌ Pendiente"
        return val
    df_res["Estado"] = df_res["Estado"].apply(limpiar)

    # Mostrar tabla con bordes HTML
    st.markdown(f"""
        <div style="overflow-x:auto; background: white; padding: 10px; border-radius: 10px;">
            <style>
                .res-table {{ width:100%; border-collapse: collapse; color: black !important; }}
                .res-table th, .res-table td {{ border: 1px solid #333 !important; padding: 12px; text-align: left; font-size: 14px; }}
                .res-table th {{ background: #eee; font-weight: bold; }}
            </style>
            <table class="res-table">
                <thead><tr><th>Actividad</th><th>Estado</th></tr></thead>
                <tbody>
                    {''.join([f'<tr><td>{row["Actividad"]}</td><td>{row["Estado"]}</td></tr>' for _, row in df_res.iterrows()])}
                </tbody>
            </table>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("⬅️ REALIZAR OTRA CONSULTA"):
        st.session_state.pantalla = 'matricula'
        st.rerun()
