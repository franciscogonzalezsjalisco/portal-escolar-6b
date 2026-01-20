import streamlit as st
import pandas as pd
import requests
import time
import re
from urllib.parse import quote

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

# --- FUNCIÓN: BITÁCORA DE CONSULTAS (Invisible para el usuario) ---
def registrar_consulta_bitacora(matricula, hoja):
    # URL de envío de tu formulario específico
    FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfBv6p1-S-zL3Q6X_mF-nS_W7fXG8-b-K_V-z-qZ-B-w-Z-fQ/formResponse"
    
    # Payload con los IDs que extrajimos de tu HTML
    payload = {
        "entry.1768815482": matricula,  # Campo de Matrícula
        "entry.499470000": hoja        # Campo para saber qué semana consultó
    }
    
    try:
        requests.post(FORM_URL, data=payload)
    except:
        pass # Si falla el registro, la app sigue funcionando normal

# --- FUNCIÓN: DETECTAR HOJAS AUTOMÁTICAMENTE ---
@st.cache_data(ttl=600)
def obtener_nombres_hojas(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    try:
        r = requests.get(url)
        encontrados = re.findall(r'\"name\":\"(.*?)\"', r.text)
        hojas = []
        for h in encontrados:
            if h and h not in ['null', 'None', 'true', 'false'] and h not in hojas:
                h_limpio = h.encode().decode('unicode_escape').strip()
                if 0 < len(h_limpio) < 50:
                    hojas.append(h_limpio)
        return hojas if hojas else ["S1 Enero"]
    except:
        return ["S1 Enero"]

# --- FUNCIÓN: CARGAR DATOS ---
@st.cache_data(ttl=0) 
def cargar_datos(nombre_hoja):
    t = int(time.time())
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={t}"
    data = pd.read_csv(url)
    data.columns = [str(col).strip() for col in data.columns]
    return data

try:
    listado_hojas = obtener_nombres_hojas(SHEET_ID)

    with st.sidebar:
        st.header("📅 Ciclo Escolar")
        hoja_sel = st.selectbox("Selecciona la semana:", listado_hojas)
        if st.button("🔄 Forzar actualización"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        st.info(f"Hoja detectada: {hoja_sel}")

    df = cargar_datos(hoja_sel)

    st.title("🏫 Portal de Consulta - 6° B")
    st.subheader(f"📍 Reporte: {hoja_sel}")
    st.markdown("---")

    matricula_input = st.text_input("Ingresa la matrícula del alumno:", placeholder="Ej. 18066902")

    if matricula_input:
        col_mat = [c for c in df.columns if "MATRICULA" in c.upper()]
        
        if col_mat:
            df['MAT_BUSCAR'] = df[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
            fila = df[df['MAT_BUSCAR'] == matricula_input.strip()]

            if not fila.empty:
                datos_alumno = fila.iloc[0]
                nombre = f"{datos_alumno.get('NOMBRE', '')} {datos_alumno.get('PATERNO', '')}"
                st.success(f"Información de: **{nombre}**")
                
                # EJECUCIÓN DE LA BITÁCORA
                registrar_consulta_bitacora(matricula_input, hoja_sel)
                
                # TABLA DE RESULTADOS
                columnas_omitir = ['NOMBRE', 'PATERNO', 'MATRICULA', 'MAT_BUSCAR', 'ALUMNO_COMPLETO']
                alumno_tabla = fila.drop(columns=[c for c in columnas_omitir if c in fila.columns])
                
                resumen = alumno_tabla.T
                resumen.columns = ["Estado"]

                def formatear(val, nombre_fila):
                    v_str = str(val).upper().strip()
                    if "CALIFICACIÓN SEMANAL" in str(nombre_fila).upper():
                        try:
                            return f"{float(val):.1f}", 'background-color: #E3F2FD; font-weight: bold; color: #1565C0;'
                        except:
                            return val, ''
                    if v_str in ['0', '0.0', 'FALSE', 'FALSO', 'NAN', '', '0']:
                        return "❌ Pendiente", 'background-color: #ffcccc; color: #990000; font-weight: bold;'
                    if v_str in ['1', '1.0', 'TRUE', 'VERDADERO']:
                        return "✅ Completado", 'background-color: #ccffcc; color: #006600;'
                    return str(val).replace('.0', ''), ''

                tabla_estilo = resumen.copy()
                estilos = []
                for n_fila, row in resumen.iterrows():
                    texto, css = formatear(row["Estado"], n_fila)
                    tabla_estilo.at[n_fila, "Estado"] = texto
                    estilos.append(css)

                st.table(tabla_estilo.style.apply(lambda x: estilos, axis=0))
            else:
                st.error("Matrícula no encontrada.")
        else:
            st.error("No se encontró la columna 'MATRICULA'.")

except Exception as e:
    st.error(f"Error de conexión: {e}")
