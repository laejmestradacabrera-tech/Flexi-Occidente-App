import streamlit as st
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Configuración de página para el Módulo Estratégico
st.set_page_config(page_title="Módulo Estratégico - Flexi Occidente", layout="wide", page_icon="🧠")

st.markdown("<h1 style='text-align: center; color: #0B1120;'>🧠 MÓDULO DE DECISIONES ESTRATÉGICAS</h1>", unsafe_allow_html=True)

# --- SEGURIDAD Y ACCESO ---
# Este módulo se visualiza junto al operativo, pero requiere autenticación para desbloquear el análisis
clave = st.text_input("🔑 Ingresa Clave Directiva para acceder al análisis profundo:", type="password")
acceso_concedido = (clave == "T5604b")

if acceso_concedido:
    st.success("✅ Acceso Directivo Confirmado.")
    tab1, tab2, tab3 = st.tabs(["🎯 Monitor Estratégico", "📊 Cruce Bitácora vs Ventas", "📦 Inventario"])
    
    # --- PESTAÑA 1: MONITOR CON CONEXIÓN A SHEETS ---
    with tab1:
        st.header("🎯 Monitor Estratégico (Conexión Maestra)")
        if st.button("Sincronizar Datos de Google Sheets"):
            with st.spinner("Conectando con la base de datos central..."):
                try:
                    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
                    # Las credenciales se gestionan desde los secretos de Streamlit en la nube
                    creds = ServiceAccountCredentials.from_json_keyfile_name('service-account.json', scope)
                    client = gspread.authorize(creds)
                    
                    archivo = client.open_by_key('1lGlVEBgu9QsrH9PYTTuoRKQeWnYiR7OwUElCsfkDgoM')
                    sheet = archivo.get_worksheet(0)
                    datos = sheet.get_all_values()
                    
                    df = pd.DataFrame(datos[1:], columns=datos[0])
                    st.success("¡Sincronización Exitosa!")
                    st.dataframe(df)
                except Exception as e:
                    st.error(f"Error en la conexión con la Nube: {e}")

    # --- PESTAÑA 2: CRUCE BITÁCORA ---
    with tab2:
        st.header("📊 Cruce Bitácora vs Ventas")
        try:
            # Lectura del archivo de ventas gestionado en el repositorio
            df_ventas = pd.read_excel("Ventas.xlsx")
            st.write("### Análisis de Ventas Registradas")
            st.dataframe(df_ventas.head())
            
            # Filtro para análisis gerencial
            tienda_sel = st.selectbox("Seleccionar Tienda para Análisis:", df_ventas['TIENDA'].unique())
            st.metric(f"Total Registros Ventas - {tienda_sel}:", len(df_ventas[df_ventas['TIENDA'] == tienda_sel]))
        except FileNotFoundError:
            st.error("El archivo 'Ventas.xlsx' no se encuentra en el repositorio.")

    # --- PESTAÑA 3: INVENTARIO ---
    with tab3:
        st.header("📦 Inventario Sin Movimiento")
        st.info("Módulo de análisis de estancamiento en desarrollo.")

elif clave != "":
    st.error("❌ Clave incorrecta. Acceso restringido a Gerencia Comercial.")
else:
    st.info("ℹ️ Por favor, ingrese su clave para desplegar las herramientas de decisión estratégica.")
