import streamlit as st
import pandas as pd
import os

# CONFIGURACIÓN
st.set_page_config(page_title="Occidente 360", layout="wide")
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📱 OCCIDENTE 360</h1>", unsafe_allow_html=True)

def cargar_datos():
    # Buscamos cualquier archivo que tenga 'Conversion' en el nombre dentro de GitHub
    archivos = [f for f in os.listdir('.') if 'Conversion' in f and f.endswith('.xlsx')]
    
    if archivos:
        # Tomamos el archivo más reciente de la lista
        f_conv = sorted(archivos)[-1]
        df = pd.read_excel(f_conv)
        # Limpieza básica
        df = df[~df['Tienda'].astype(str).str.contains('3004|3015|Total')].copy()
        df['Conv%'] = df['Conv. Año Actual'].apply(lambda x: x*100 if x < 1 else x)
        df['Uds_Tkt'] = df['Ticket prom. Actual']
        return df, f_conv
    return None, None

df, file_name = cargar_datos()

if df is not None:
    meta_objetivo = 10.9
    en_meta = df[df['Conv%'] >= meta_objetivo].shape[0]
    bajo_meta = df[df['Conv%'] < meta_objetivo].shape[0]
    
    c1, c2 = st.columns(2)
    c1.metric("🟢 EN META", f"{en_meta} Tiendas")
    c2.metric("🔴 BAJO META", f"{bajo_meta} Tiendas")
    
    st.markdown("---")
    st.subheader(f"🏆 RANKING DE CONVERSIÓN")
    st.write(f"Archivo analizado: {file_name}")
    
    # Mostrar tabla con colores
    st.dataframe(df[['Tienda', 'Conv%', 'Uds_Tkt']].sort_values('Conv%', ascending=False))
else:
    st.error("⚠️ No encontré el archivo de Excel. Asegúrate de haberlo subido a GitHub con el nombre 'Conversion...'")
   
