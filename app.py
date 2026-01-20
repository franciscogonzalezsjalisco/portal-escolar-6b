import streamlit as st
import pandas as pd
import ssl
from urllib.parse import quote

# 1. CONFIGURACIÓN INICIAL
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

st.set_page_config(page_title="Urbana 690. Portal Escolar 6°B", layout="centered")

# 2. IDENTIFICACIÓN DEL DOCUMENTO
SHEET_ID = "1-WhenbF_94yLK556stoWxLlKBpmP88UTfYip5BaygFM"

# DICCIONARIO DE HOJAS (Nombre exacto: ID de la hoja)
# Nota: El gid=0 suele ser la primera hoja. 
# Si creaste las otras después, tienen números largos.
# Vamos a usar la búsqueda por nombre con un ajuste de URL más potente.
MIS_HOJAS = ["S1 Enero", "S2 Enero", "S3 Enero", "S1 Febrero"]

@st.cache_data(ttl=600) # Se actualiza cada 10 minutos
def cargar_datos(nombre_hoja):
    # Usamos una URL de exportación más directa y "limpia"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(nombre_hoja)}"
    data = pd.read_csv(url)
    # Limpieza profunda de nombres de columnas
    data.columns = [str(col).strip() for col in data.columns]
    # Crear columna para el buscador
    if 'NOMBRE' in data.columns and 'PATERNO' in data.columns:
        data['ALUMNO_COMPLETO'] = data['NOMBRE'].astype(str).strip() + " " + data['PATERNO'].astype(str).strip()
    return data

try:
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("📅 Ciclo Escolar")
        hoja_sel = st.selectbox("Selecciona la semana de consulta:", MIS_HOJAS)
        st.divider()
        st.caption("Nota: Si la información no cambia, intenta refrescar la página.")

    # Intentar cargar datos
    df = cargar_datos(hoja_sel)

    st.title("🏫 Portal de Consulta - 6° B")
    st.subheader(f"📍 Registro de: {hoja_sel}")
    st.markdown("---")

    # 3. BUSCADOR DE ALUMNOS
    if 'ALUMNO_COMPLETO' in df.columns:
        nombres_lista = sorted(df['ALUMNO_COMPLETO'].unique())
        nombre_seleccionado = st.selectbox(
            "Selecciona el nombre del alumno:", 
            options=["-- Haz clic aquí para buscar --"] + nombres_lista
        )

        if nombre_seleccionado != "-- Haz clic aquí para buscar --":
            fila = df[df['ALUMNO_COMPLETO'] == nombre_seleccionado]

            if not fila.empty:
                st.success(f"Mostrando resultados de: **{nombre_seleccionado}**")
                
                # 4. TABLA DE RESULTADOS
                columnas_ignorar = ['ALUMNO_COMPLETO', 'MAT_STR', 'MATRICULA_STR', 'MAT_BUSCAR']
                alumno_final = fila.drop(columns=[c for c in columnas_ignorar if c in fila.columns])
                
                resumen = alumno_final.T
                resumen.columns = ["Estado"]

                def formatear(val, nombre_fila):
                    v_str = str(val).upper().strip()
                    
                    # Caso: Calificación Semanal (Redondeo a 1 decimal)
                    if "CALIFICACIÓN SEMANAL" in str(nombre_fila).upper():
                        try:
                            return f"{float(val):.1f}", 'background-color: #E3F2FD; font-weight: bold; color: #1565C0;'
                        except:
                            return val, ''

                    # Caso: Tareas Pendientes/Completadas
                    if v_str in ['0', '0.0', 'FALSE', 'FALSO', 'NAN', '']:
                        return "❌ Pendiente", 'background-color: #ffcccc; color: #990000; font-weight: bold;'
                    if v_str in ['1', '1.0', 'TRUE', 'VERDADERO']:
                        return "✅ Completado", 'background-color: #ccffcc; color: #006600;'
                    
                    # Otros números o textos
                    return str(val).replace('.0', ''), ''

                tabla_estilada = resumen.copy()
                estilos = []
                
                for nombre_fila, row in resumen.iterrows():
                    texto, css = formatear(row["Estado"], nombre_fila)
                    tabla_estilada.at[nombre_fila, "Estado"] = texto
                    estilos.append(css)

                st.table(tabla_estilada.style.apply(lambda x: estilos, axis=0))
            else:
                st.warning("No se encontraron datos para esta selección.")
    else:
        st.error(f"Error: La pestaña '{hoja_sel}' no tiene las columnas NOMBRE y PATERNO.")

except Exception as e:
    st.error(f"Hubo un problema al conectar con la hoja: {e}")
    st.info("Asegúrate de que los nombres de las pestañas en Excel coincidan exactamente con el menú de la izquierda.")
