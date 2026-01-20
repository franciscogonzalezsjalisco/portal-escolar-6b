import streamlit as st
import pandas as pd
import requests
import time
from urllib.parse import quote

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

# --- FUNCIÓN: DETECTAR HOJAS (MÉTODO ROBUSTO) ---
@st.cache_data(ttl=300)
def obtener_nombres_hojas(sheet_id):
    # Usamos el endpoint de exportación a Excel para leer los nombres de las pestañas
    # Este método es mucho más estable que leer el HTML
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        # Leemos el archivo temporalmente solo para extraer los nombres de las hojas
        xls = pd.ExcelFile(url)
        return xls.sheet_names
    except Exception as e:
        st.error(f"Error al detectar pestañas: {e}")
        return ["S1 Enero"] # Valor por defecto si algo falla

# --- FUNCIÓN: BITÁCORA DE CONSULTAS ---
def registrar_consulta_bitacora(matricula, hoja):
    # URL de envío de tu formulario
    FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfBv6p1-S-zL3Q6X_mF-nS_W7fXG8-b-K_V-z-qZ-B-w-Z-fQ/formResponse"
    payload = {
        "entry.1768815482": str(matricula),
        "entry.499470000": str(hoja)
    }
    try:
        requests.post(FORM_URL, data=payload, timeout=5)
    except:
        pass

# --- FUNCIÓN: CARGAR DATOS DE LA HOJA SELECCIONADA ---
@st.cache_data(ttl=0) 
def cargar_datos(nombre_hoja):
    t = int(time.time())
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}&t={t}"
    data = pd.read_csv(url)
    data.columns = [str(col).strip() for col in data.columns]
    return data

# --- LÓGICA PRINCIPAL ---
try:
    # 1. Obtener todas las hojas automáticamente
    listado_hojas = obtener_nombres_hojas(SHEET_ID)

    with st.sidebar:
        st.header("📅 Ciclo Escolar")
        hoja_sel = st.selectbox("Selecciona la semana:", listado_hojas)
        
        if st.button("🔄 Actualizar Todo"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        st.caption(f"Hojas encontradas: {len(listado_hojas)}")

    # 2. Cargar datos de la hoja que el usuario eligió
    df = cargar_datos(hoja_sel)

    st.title("🏫 Portal de Consulta - 6° B")
    st.subheader(f"📍 Reporte: {hoja_sel}")
    st.markdown("---")

    matricula_input = st.text_input("Ingresa la matrícula del alumno:", placeholder="Ej. 18066902")

    if matricula_input:
        # Buscamos la columna de matrícula
        col_mat = [c for c in df.columns if "MATRICULA" in c.upper()]
        
        if col_mat:
            # Limpiamos datos para la búsqueda
            df['MAT_BUSCAR'] = df[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
            fila = df[df['MAT_BUSCAR'] == matricula_input.strip()]

            if not fila.empty:
                datos_alumno = fila.iloc[0]
                nombre_completo = f"{datos_alumno.get('NOMBRE', '')} {datos_alumno.get('PATERNO', '')}"
                st.success(f"Información de: **{nombre_completo}**")
                
                # Registro en bitácora
                registrar_consulta_bitacora(matricula_input, hoja_sel)
                
                # Preparar tabla (omitir columnas internas)
                columnas_omitir = ['NOMBRE', 'MATERNO', 'PATERNO', 'MATRICULA', 'MAT_BUSCAR', 'ALUMNO_COMPLETO']
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
            st.error("No se detectó la columna 'MATRICULA' en esta hoja.")

except Exception as e:
    st.error(f"Hubo un detalle: {e}")
