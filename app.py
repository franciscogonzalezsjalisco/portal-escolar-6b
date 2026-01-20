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
MIS_HOJAS = ["S1 Enero", "S2 Enero", "S3 Enero", "S1 Febrero"]

@st.cache_data(ttl=300) # Se actualiza cada 5 minutos
def cargar_datos(nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}"
    data = pd.read_csv(url)
    # Limpieza de encabezados
    data.columns = [str(col).strip() for col in data.columns]
    
    # CORRECCIÓN DEL ERROR: Usamos .str.strip() para columnas de texto
    if 'NOMBRE' in data.columns and 'PATERNO' in data.columns:
        nombres = data['NOMBRE'].astype(str).str.strip()
        paternos = data['PATERNO'].astype(str).str.strip()
        data['ALUMNO_COMPLETO'] = nombres + " " + paternos
    return data

try:
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("📅 Ciclo Escolar")
        hoja_sel = st.selectbox("Selecciona la semana de consulta:", MIS_HOJAS)
        st.divider()
        st.caption("Si cambias de semana y no ves datos, refresca la página.")

    df = cargar_datos(hoja_sel)

    st.title("🏫 Portal de Consulta - 6° B")
    st.subheader(f"📍 Registro de: {hoja_sel}")
    st.markdown("---")

    # 3. BUSCADOR DE ALUMNOS
    if 'ALUMNO_COMPLETO' in df.columns:
        # Quitamos posibles valores vacíos y ordenamos
        nombres_lista = sorted(df['ALUMNO_COMPLETO'].dropna().unique())
        nombre_seleccionado = st.selectbox(
            "Selecciona el nombre del alumno:", 
            options=["-- Haz clic aquí para buscar --"] + nombres_lista
        )

        if nombre_seleccionado != "-- Haz clic aquí para buscar --":
            fila = df[df['ALUMNO_COMPLETO'] == nombre_seleccionado]

            if not fila.empty:
                st.success(f"Resultados para: **{nombre_seleccionado}**")
                
                # 4. TABLA DE RESULTADOS
                columnas_ignorar = ['ALUMNO_COMPLETO', 'MATRICULA', 'MAT_STR', 'MATRICULA_STR', 'MAT_BUSCAR']
                alumno_final = fila.drop(columns=[c for c in columnas_ignorar if c in fila.columns])
                
                resumen = alumno_final.T
                resumen.columns = ["Estado"]

                def formatear(val, nombre_fila):
                    v_str = str(val).upper().strip()
                    
                    # Calificación Semanal (Redondeo a 1 decimal)
                    if "CALIFICACIÓN SEMANAL" in str(nombre_fila).upper():
                        try:
                            return f"{float(val):.1f}", 'background-color: #E3F2FD; font-weight: bold; color: #1565C0;'
                        except:
                            return val, ''

                    # Tareas Pendientes/Completadas
                    if v_str in ['0', '0.0', 'FALSE', 'FALSO', 'NAN', '', '0']:
                        return "❌ Pendiente", 'background-color: #ffcccc; color: #990000; font-weight: bold;'
                    if v_str in ['1', '1.0', 'TRUE', 'VERDADERO']:
                        return "✅ Completado", 'background-color: #ccffcc; color: #006600;'
                    
                    return str(val).replace('.0', ''), ''

                tabla_estilada = resumen.copy()
                estilos = []
                
                for n_fila, row in resumen.iterrows():
                    texto, css = formatear(row["Estado"], n_fila)
                    tabla_estilada.at[n_fila, "Estado"] = texto
                    estilos.append(css)

                st.table(tabla_estilada.style.apply(lambda x: estilos, axis=0))
            else:
                st.warning("No hay datos para este alumno.")
    else:
        st.error(f"Revisa la hoja '{hoja_sel}': falta la columna NOMBRE o PATERNO.")

except Exception as e:
    st.error(f"Ocurrió un detalle al cargar la información: {e}")
