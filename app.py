import streamlit as st
import pandas as pd
import ssl
from urllib.parse import quote

# 1. CONFIGURACIÓN
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

st.set_page_config(page_title="Portal Escolar 6°B", layout="centered")

# 2. CONFIGURACIÓN DEL DOCUMENTO
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

# NOMBRES DE TUS HOJAS (Asegúrate que coincidan exactamente con tu Excel)
MIS_HOJAS = ["S1 Enero", "S2 Enero", "S3 Enero", "S1 Febrero"] 

@st.cache_data
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
        st.info(f"Visualizando: {hoja_sel}")

    df = cargar_datos(hoja_sel)

    st.title("🏫 Portal de Consulta - 6° B")
    st.subheader(f"📍 Registro: {hoja_sel}")
    st.markdown("---")

    # 3. BUSCADOR POR MATRÍCULA
    matricula_input = st.text_input("Ingresa la matrícula del alumno:", placeholder="Ej. 18066902")

    if matricula_input:
        col_mat = [c for c in df.columns if "MATRICULA" in c.upper()]
        
        if col_mat:
            df['MAT_BUSCAR'] = df[col_mat[0]].astype(str).str.replace('.0', '', regex=False).str.strip()
            fila = df[df['MAT_BUSCAR'] == matricula_input.strip()]

            if not fila.empty:
                datos = fila.iloc[0]
                nombre_completo = f"{datos.get('NOMBRE', '')} {datos.get('PATERNO', '')}"
                st.success(f"Alumno: **{nombre_completo}**")
                
                # 4. TABLA DE RESULTADOS
                resumen = fila.drop(columns=['MAT_BUSCAR']).T
                resumen.columns = ["Estado"]

                # 5. FUNCIÓN DE FORMATO CON REDONDEO PARA CALIFICACIÓN
                def formatear(val, nombre_fila):
                    v_str = str(val).upper().strip()
                    
                    # Lógica para Calificación Semanal (1 decimal)
                    if "CALIFICACIÓN SEMANAL" in str(nombre_fila).upper():
                        try:
                            numero = float(val)
                            return f"{numero:.1f}", 'background-color: #E3F2FD; font-weight: bold; color: #1565C0;'
                        except:
                            return val, ''

                    # Lógica para Pendientes/Completados
                    if v_str in ['0', '0.0', 'FALSE', 'FALSO', 'NAN']:
                        return "❌ Pendiente", 'background-color: #ffcccc; color: #990000; font-weight: bold;'
                    if v_str in ['1', '1.0', 'TRUE', 'VERDADERO']:
                        return "✅ Completado", 'background-color: #ccffcc; color: #006600;'
                    
                    # Quitar el .0 a números que no son calificación (ej. Matrícula)
                    return str(val).replace('.0', ''), ''

                tabla_final = resumen.copy()
                estilos = []
                
                # Recorremos la tabla usando el nombre de la fila para saber si es la calificación
                for nombre_fila, row in resumen.iterrows():
                    texto, css = formatear(row["Estado"], nombre_fila)
                    tabla_final.at[nombre_fila, "Estado"] = texto
                    estilos.append(css)

                st.table(tabla_final.style.apply(lambda x: estilos, axis=0))
            else:
                st.error("No se encontró esa matrícula en esta hoja.")
        else:
            st.error("Error: No se encontró la columna 'MATRICULA'.")

except Exception as e:
    st.error(f"Error al cargar la hoja: {e}")