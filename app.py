import streamlit as st
import pandas as pd
import ssl
from urllib.parse import quote

# 1. CONFIGURACIÓN INICIAL
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

# 2. IDENTIFICACIÓN DEL DOCUMENTO
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"
MIS_HOJAS = ["S1 Enero", "S2 Enero", "S3 Enero", "S4 Enero"]

@st.cache_data(ttl=300)
def cargar_datos(nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}"
    data = pd.read_csv(url)
    data.columns = [str(col).strip() for col in data.columns]
    return data

try:
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("📅 Ciclo Escolar")
        hoja_sel = st.selectbox("Selecciona la semana:", MIS_HOJAS)
        st.divider()
        st.info(f"Semana activa: {hoja_sel}")

    df = cargar_datos(hoja_sel)

    st.title("🏫 Portal de Consulta - 6° B")
    st.subheader(f"📍 Reporte: {hoja_sel}")
    st.markdown("---")

    # 3. SEGURIDAD: CONSULTA POR MATRÍCULA
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
                
                # 4. TABLA DE RESULTADOS (Omitiendo datos ya mencionados)
                columnas_a_omitir = ['NOMBRE', 'PATERNO', 'MATRICULA', 'MAT_BUSCAR', 'ALUMNO_COMPLETO']
                alumno_tabla = fila.drop(columns=[c for c in columnas_a_omitir if c in fila.columns])
                
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

                # --- BLOQUE CORREGIDO (SANGRÍA) ---
                tabla_estilo = resumen.copy()
                estilos = []
                
                # Estas líneas DEBEN tener 16 espacios o 4 tabulaciones de margen
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
