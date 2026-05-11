import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Occidente 360", layout="wide")
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📱 OCCIDENTE 360</h1>", unsafe_allow_html=True)

def cargar_datos():
    # Buscamos el archivo Excel
    archivos = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    if archivos:
        f_conv = sorted(archivos)[-1]
        df = pd.read_excel(f_conv)
        
        # Intentamos detectar las columnas correctas sin importar mayúsculas/minúsculas
        df.columns = [c.strip() for c in df.columns] # Limpiamos espacios
        
        # Buscamos la columna de Tienda y de Conversión
        col_tienda = next((c for c in df.columns if 'Tienda' in c or 'TIENDA' in c), None)
        col_conv = next((c for c in df.columns if 'Conv' in c and 'Actual' in c), None)
        col_tkt = next((c for c in df.columns if 'Ticket' in c or 'Uds' in c), None)

        if col_tienda and col_conv:
            # Limpiamos filas vacías o de totales
            df = df[df[col_tienda].notna()]
            df = df[~df[col_tienda].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)].copy()
            
            # Ajustamos el porcentaje
            df['Conv_Mostrar'] = df[col_conv].apply(lambda x: x*100 if x < 1 else x)
            return df, f_conv, col_tienda, 'Conv_Mostrar', col_tkt
            
    return None, None, None, None, None

df, file_name, c_tienda, c_conv, c_tkt = cargar_datos()

if df is not None:
    st.success(f"✅ Archivo detectado: {file_name}")
    
    # Métricas principales
    meta = 10.9
    en_meta = df[df[c_conv] >= meta].shape[0]
    bajo_meta = df[df[c_conv] < meta].shape[0]
    
    col1, col2 = st.columns(2)
    col1.metric("🟢 EN META", f"{en_meta} Tiendas")
    col2.metric("🔴 BAJO META", f"{bajo_meta} Tiendas")
    
    st.markdown("---")
    st.subheader("🏆 TOP 20 - RANKING DE CONVERSIÓN")
    
    # Creamos el ranking
    columnas_top = [c_tienda, c_conv]
    if c_tkt: columnas_top.append(c_tkt)
    
    top_20 = df[columnas_top].sort_values(c_conv, ascending=False).head(20)
    
    # Mostramos la tabla
    st.table(top_20.style.format({c_conv: '{:.2f}%'}))
else:
    st.warning("⚠️ El archivo se cargó, pero no encuentro las columnas de 'Tienda' o 'Conversión'. Revisa que el Excel tenga esos títulos.")
