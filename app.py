import streamlit as st
import pandas as pd
import time
from urllib.parse import quote

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

# --- INICIALIZAR MEMORIA ---
if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'matricula_guardada' not in st.session_state: st.session_state.matricula_guardada = ""
if 'alumno_datos' not in st.session_state: st.session_state.alumno_datos = None

URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

# 2. CSS ACTUALIZADO (Con estilos para la Boleta)
st.markdown(f"""
    <style>
    .stApp {{
        background: white !important;
        background: linear-gradient(rgba(255,255,255,0.7), rgba(255,255,255,0.7)), url("{URL_FONDO}") !important;
        background-size: cover !important;
        background-attachment: fixed !important;
    }}
    h1, h2, h3, p, label, span, div {{ color: black !important; }}
    
    /* Contenedor de la Boleta para Captura */
    .boleta-container {{
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 3px solid #1D3557;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }}
    
    /* Estilo de la Barra de Progreso Personalizada */
    .stProgress > div > div > div > div {{
        background-color: #2A9D8F !important;
    }}
    
    /* Botones vibrantes */
    div.stButton > button {{
        width: 100% !important; height: 60px !important;
        border-radius: 12px !important; font-weight: 900 !important;
        color: white !important; text-transform: uppercase !important;
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
                color_v = colores[idx % len(colores)]
                with cols[j]:
                    st.markdown(f'<style>button[key="btn_{idx}"] {{ background-color: {color_v} !important; }}</style>', unsafe_allow_html=True)
                    if st.button(nombre_h, key=f"btn_{idx}"):
                        st.session_state.semana_activa = nombre_h
                        st.session_state.pantalla = 'matricula'
                        st.rerun()

# --- PANTALLA 2: MATRÍCULA ---
elif st.session_state.pantalla == 'matricula':
    st.title(f"📍 {st.session_state.semana_activa}")
    mat_input = st.text_input("Ingresa la matrícula:", value=st.session_state.matricula_guardada)
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
                else: st.error("Matrícula no encontrada.")
    if st.button("⬅️ VOLVER AL MENÚ"):
        st.session_state.pantalla = 'inicio'
        st.rerun()

# --- PANTALLA 3: RESULTADOS (ESTÉTICA MEJORADA) ---
elif st.session_state.pantalla == 'resultados':
    datos = st.session_state.alumno_datos
    
    # 1. PROCESAR DATOS Y CALCULAR PROGRESO
    omitir = ['NOMBRE', 'PATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    res_filtrado = {k: v for k, v in datos.items() if k.upper() not in omitir}
    
    total_tareas = len(res_filtrado)
    entregadas = sum(1 for v in res_filtrado.values() if str(v).upper().strip() in ['1', '1.0', 'TRUE', 'VERDADERO'])
    porcentaje = int((entregadas / total_tareas) * 100) if total_tareas > 0 else 0
    
    # 2. DETERMINAR MENSAJE PERSONALIZADO
    if porcentaje == 100:
        mensaje = "🌟 ¡Excelente trabajo! Has cumplido con todo. ¡Sigue así!"
        color_msg = "#D4AF37" # Dorado
    elif porcentaje >= 80:
        mensaje = "✅ ¡Muy bien! Casi terminas todo, falta muy poco."
        color_msg = "#2A9D8F"
    elif porcentaje >= 50:
        mensaje = "⚠️ Vas por buen camino, pero aún tienes pendientes."
        color_msg = "#F4A261"
    else:
        mensaje = "🚩 ¡Atención! Tienes muchas actividades pendientes por entregar."
        color_msg = "#E63946"

    # 3. MOSTRAR BOLETA
    st.markdown(f"""
        <div class="boleta-container">
            <h2 style='text-align: center; color: #1D3557;'>REPORTE SEMANAL</h2>
            <p style='text-align: center; font-size: 1.2em;'>🎓 <b>Alumno:</b> {datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}</p>
            <hr>
            <p style='margin-bottom: 5px;'><b>Progreso de cumplimiento: {porcentaje}%</b></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.progress(porcentaje / 100)
    
    st.markdown(f"""
        <div style='background-color: {color_msg}22; padding: 15px; border-radius: 10px; border-left: 5px solid {color_msg}; margin: 15px 0;'>
            <p style='margin: 0; font-weight: bold; color: {color_msg};'>{mensaje}</p>
        </div>
    """, unsafe_allow_html=True)

    # Tabla de resultados
    df_res = pd.DataFrame(res_filtrado.items(), columns=["Actividad", "Estado"])
    df_res["Estado"] = df_res["Estado"].apply(lambda x: "✅ Completado" if str(x).upper().strip() in ['1', '1.0', 'TRUE'] else "❌ Pendiente")
    
    st.table(df_res)
    
    st.info("📸 **Tip:** Puedes tomar una captura de pantalla de esta sección para guardar tu reporte.")
    
    if st.button("⬅️ REALIZAR OTRA CONSULTA"):
        st.session_state.pantalla = 'matricula'
        st.rerun()
