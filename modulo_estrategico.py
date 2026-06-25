import streamlit as st
import pandas as pd
import os

# Configuración única
st.set_page_config(page_title="Flexi Occidente - Sistema Integral", layout="wide")

# Menú lateral para separar Operativo de Estratégico
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Selecciona el módulo:", ["Operativo", "Estratégico"])

if opcion == "Operativo":
    st.title("📌 Bitácora Operativa")
    st.write("---")
    st.write("Bienvenido al registro operativo diario.")
    # AQUÍ IRÁ EL CÓDIGO DE TU BITÁCORA QUE YA TIENES FUNCIONANDO

elif opcion == "Estratégico":
    st.title("🧠 Módulo de Decisiones Estratégicas")
    st.write("---")
    clave = st.text_input("🔑 Ingresa Clave Directiva:", type="password")
    
    if clave == "T5604b":
        st.success("✅ Acceso Directivo Confirmado.")
        
        # Pestañas solo visibles si la clave es correcta
        tab1, tab2 = st.tabs(["🎯 Monitor Estratégico", "📊 Cruce de Ventas"])
        
        with tab1:
            st.subheader("Monitor de Google Sheets")
            st.write("Conexión con base de datos maestra activa.")
            # Lógica de Google Sheets aquí
            
        with tab2:
            st.subheader("Análisis de Ventas")
            if os.path.exists("Ventas.xlsx"):
                st.dataframe(pd.read_excel("Ventas.xlsx").head())
            else:
                st.error("Archivo 'Ventas.xlsx' no encontrado.")
    
    elif clave != "":
        st.error("❌ Clave incorrecta. Acceso restringido.")
