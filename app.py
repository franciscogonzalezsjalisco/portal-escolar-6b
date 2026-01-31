import streamlit as st
import pandas as pd
import time
from urllib.parse import quote

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

# --- INICIALIZAR MEMORIA (Añadimos 'alumno_datos') ---
if 'pantalla' not in st.session_state: st.session_state.pantalla = 'inicio'
if 'semana_activa' not in st.session_state: st.session_state.semana_activa = None
if 'matricula_guardada' not in st.session_state: st.session_state.matricula_guardada = ""
if 'alumno_datos' not in st.session_state: st.session_state.alumno_datos = None

URL_FONDO = "https://raw.githubusercontent.com/franciscogonzalezsjalisco/portal-escolar-6b/main/6b.png"
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

# 2. CSS PARA BOTONES HOMOGÉNEOS Y VISIBILIDAD
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(255,255,255,0.75), rgba(255,255,255,0.75)), url("{URL_FONDO}");
        background-size: cover;
        background-attachment: fixed;
    }}
    h1, h2, h3, p, label {{ color: #000000 !important; font-family: 'Arial', sans-serif; }}
    
    .stButton > button {{
        width: 100% !important; height: 80px !important;
        border-radius: 15px !important; color: white !important;
        font-size: 18px !important; font-weight: bold !important;
        text-transform: uppercase; border: none !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }}
    /* Estilo especial para el botón de 'Volver' para que no sea tan gigante */
    .bot-volver > div > button {{
        height: 50px !important; background-color: #607D8B !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. FUNCIONES
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
    st.markdown("### 📅 Selecciona la semana a consultar")
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
    st.markdown(f"## 📍 {st.session_state.semana_activa}")
    st.markdown("---")
    
    mat_input = st.text_input("Introduce la matrícula del alumno:", value=st.session_state.matricula_guardada)
    st.session_state.matricula_guardada = mat_input

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="bot-volver">', unsafe_allow_html=True)
        if st.button("⬅️ MENÚ"):
            st.session_state.pantalla = 'inicio'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        if st.button("🔍 CONSULTAR"):
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

# --- PANTALLA 3: INFORMACIÓN DETALLADA (RESULTADOS) ---
elif st.session_state.pantalla == 'resultados':
    datos = st.session_state.alumno_datos
    st.balloons()
    
    st.success(f"### 🎓 {datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}")
    
    # --- ESTILO ESPECÍFICO PARA LA TABLA RESPONSIVA ---
    st.markdown("""
        <style>
        /* Forzar bordes y líneas en la tabla */
        table {
            width: 100%;
            border-collapse: collapse;
            border: 2px solid #333333;
            background-color: white;
            font-size: clamp(12px, 3.5vw, 16px) !important; /* Ajusta el tamaño de letra según pantalla */
        }
        th, td {
            border: 1px solid #dddddd !important;
            padding: 8px !important;
            text-align: left !important;
            color: black !important;
        }
        th {
            background-color: #f2f2f2 !important;
            font-weight: bold !important;
        }
        /* Zebra striping para lectura fácil */
        tr:nth-child(even) { background-color: #f9f9f9; }
        </style>
    """, unsafe_allow_html=True)

    # Filtrar y limpiar datos
    omitir = ['NOMBRE', 'PATERNO', 'MATRICULA', 'BUSCAR', 'ALUMNO_COMPLETO']
    res_filtrado = {k: v for k, v in datos.items() if k.upper() not in omitir}
    
    df_res = pd.DataFrame(res_filtrado.items(), columns=["Actividad", "Estado"])
    
    def limpiar_resultado(val):
        v = str(val).upper().strip()
        if v in ['1', '1.0', 'TRUE', 'VERDADERO']: return "✅ Completado"
        if v in ['0', '0.0', 'FALSE', 'FALSO', 'NAN', '']: return "❌ Pendiente"
        return val

    df_res["Estado"] = df_res["Estado"].apply(limpiar_resultado)

    # Renderizar la tabla como HTML para tener control total de los bordes
    st.write(df_res.to_html(index=False, escape=False), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ REALIZAR OTRA CONSULTA"):
        st.session_state.pantalla = 'matricula'
        st.rerun()
