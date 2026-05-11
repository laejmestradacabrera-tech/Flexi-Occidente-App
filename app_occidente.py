import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Occidente 360", layout="wide")
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📱 OCCIDENTE 360</h1>", unsafe_allow_html=True)

# Ruta de tu Drive (asegúrate de que el nombre de la carpeta sea exacto)
RUTA = '/content/drive/My Drive/Occidente360/'

def cargar_datos():
    archivos = [f for f in os.listdir(RUTA) if 'Conversion' in f and f.endswith('.xlsx')]
    if archivos:
        f_conv = sorted(archivos)[-1]
        df = pd.read_excel(RUTA + f_conv)
        df = df[~df['Tienda'].astype(str).str.contains('3004|3015|Total')].copy()
        df['Conv%'] = df['Conv. Año Actual'].apply(lambda x: x*100 if x < 1 else x)
        df['Uds_Tkt'] = df['Ticket prom. Actual']
        return df, f_conv
    return None, None

df, file_name = cargar_datos()

if df is not None:
    meta = 10.9
    v, r = df[df['Conv%'] >= meta].shape[0], df[df['Conv%'] < meta].shape[0]
    
    col1, col2 = st.columns(2)
    col1.metric("🟢 EN META", f"{v} Tiendas")
    col2.metric("🔴 BAJO META", f"{r} Tiendas")
    
    st.markdown("---")
    st.subheader("🏆 TOP 20 - RANKING DE CONVERSIÓN")
    
    top_20 = df[['Tienda', 'Conv%', 'Uds_Tkt']].sort_values('Conv%', ascending=False).head(20)
    
    def style_row(val):
        return 'background-color: #d4edda' if val >= meta else 'background-color: #f8d7da'
    
    st.table(top_20.style.format({'Conv%': '{:.2f}%', 'Uds_Tkt': '{:.2f}'})
             .applymap(style_row, subset=['Conv%']))
else:
    st.error("⚠️ Sube el archivo Excel a la carpeta 'Occidente360' en tu Drive.")
