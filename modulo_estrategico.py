import streamlit as st
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Configuración de página
st.set_page_config(page_title="Módulo Estratégico - Flexi Occidente", layout="wide", page_icon="🧠")

st.markdown("<h1 style='text-align: center; color: #0B1120;'>🧠 MÓDULO DE DECISIONES ESTRATÉGICAS</h1>", unsafe_allow_html=True)

# --- SEGURIDAD ---
clave = st.text_input("🔑 Ingresa Clave Directiva:", type="password")
acceso_concedido = (clave == "T5604b")

if acceso_concedido:
    tab1, tab2, tab3 = st.tabs(["🎯 Monitor Estratégico", "📊 Cruce Bitácora vs Ventas", "📦 Inventario"])
    
    # --- PESTAÑA 1: MONITOR CON CONEXIÓN A SHEETS ---
    with tab1:
        st.header("🎯 Monitor Estratégico (Conexión Maestra)")
        if st.button("Cargar Datos de Google Sheets"):
            with st.spinner("Sincronizando con base de datos maestra..."):
                try:
                    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
                    # Asegúrate de tener el archivo JSON de credenciales en tu carpeta
                    creds = ServiceAccountCredentials.from_json_keyfile_name('service-account.json', scope)
                    client = gspread.authorize(creds)
                    
                    archivo = client.open_by_key('1lGlVEBgu9QsrH9PYTTuoRKQeWnYiR7OwUElCsfkDgoM')
                    sheet = archivo.get_worksheet(0)
                    datos = sheet.get_all_values()
                    
                    df = pd.DataFrame(datos[1:], columns=datos[0])
                    st.success("¡Sincronización Exitosa!")
                    st.dataframe(df)
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

    # --- PESTAÑA 2: CRUCE BITÁCORA ---
    with tab2:
        st.header("📊 Cruce Bitácora vs Ventas")
        try:
            df_ventas = pd.read_excel("Ventas.xlsx")
            st.write("### Vista de Ventas")
            st.dataframe(df_ventas.head())
            tienda_sel = st.selectbox("Seleccionar Tienda", df_ventas['TIENDA'].unique())
            st.metric("Ventas:", len(df_ventas[df_ventas['TIENDA'] == tienda_sel]))
        except FileNotFoundError:
            st.error("Archivo 'Ventas.xlsx' no localizado.")

    # --- PESTAÑA 3: INVENTARIO ---
    with tab3:
        st.header("📦 Inventario Sin Movimiento")
        st.info("Módulo en fase de desarrollo.")

elif clave != "":
    st.error("Clave incorrecta. Acceso denegado.")
