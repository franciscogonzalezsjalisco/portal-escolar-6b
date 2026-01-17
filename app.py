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
# Lista de tus hojas actuales
MIS_HOJAS = ["S1 Enero", "S2 Enero", "S3 Enero", "S4 Enero"] 

@st.cache_data
def cargar_datos(nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}"
    data = pd.read_csv(url)
    # Limpiamos nombres de columnas
    data.columns = [str(col).strip() for col in data.columns]
    # Creamos una columna de Nombre Completo para el buscador
    if 'NOMBRE' in data.columns and 'PATERNO' in data.columns:
        data['ALUMNO_COMPLETO'] = data['NOMBRE'].astype(str) + " " + data['PATERNO'].astype(str)
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

    # 3. SELECCIÓN POR NOMBRE (En lugar de Matrícula)
    if 'ALUMNO_COMPLETO' in df.columns:
        # Ordenamos los nombres alfabéticamente
        nombres_lista = sorted(df['ALUMNO_COMPLETO'].unique())
        nombre_seleccionado = st.selectbox(
            "Selecciona el nombre del alumno:", 
            options=["-- Selecciona un nombre --"] + nombres_lista
        )

        if nombre_seleccionado != "-- Selecciona un nombre --":
            fila = df[df['ALUMNO_COMPLETO'] == nombre_seleccionado]

            if not fila.empty:
                st.success(f"Reporte encontrado para: **{nombre_seleccionado}**")
                
                # 4. PREPARAR TABLA DE RESULTADOS
                # Quitamos las columnas de control interno para la tabla final
                columnas_a_quitar = ['ALUMNO_COMPLETO', 'MAT_STR', 'MATRICULA_STR']
                alumno_final = fila.drop(columns=[c for c in columnas_a_quitar if c in fila.columns])
                
                resumen = alumno_final.T
                resumen.columns = ["Estado"]

                # 5. FUNCIÓN DE FORMATO (Iconos y Redondeo)
                def formatear(val, nombre_fila):
                    v_str = str(val).upper().strip()
                    
                    # Calificación Semanal con 1 decimal
                    if "CALIFICACIÓN SEMANAL" in str(nombre_fila).upper():
                        try:
                            numero = float(val)
                            return f"{numero:.1f}", 'background-color: #E3F2FD; font-weight: bold; color: #1565C0;'
                        except:
                            return val, ''

                    # Iconos para tareas
                    if v_str in ['0', '0.0', 'FALSE', 'FALSO', 'NAN']:
                        return "❌ Pendiente", 'background-color: #ffcccc; color: #990000; font-weight: bold;'
                    if v_str in ['1', '1.0', 'TRUE', 'VERDADERO']:
                        return "✅ Completado", 'background-color: #ccffcc; color: #006600;'
                    
                    return str(val).replace('.0', ''), ''

                tabla_final = resumen.copy()
                estilos = []
                
                for nombre_fila, row in resumen.iterrows():
                    texto, css = formatear(row["Estado"], nombre_fila)
                    tabla_final.at[nombre_fila, "Estado"] = texto
                    estilos.append(css)

                st.table(tabla_final.style.apply(lambda x: estilos, axis=0))
    else:
        st.error("No se encontraron las columnas 'NOMBRE' y 'PATERNO' en esta hoja.")

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
