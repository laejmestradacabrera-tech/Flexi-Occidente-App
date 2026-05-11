import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- ESTILO PERSONALIZADO (ROJO FLEXI) ---
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #E30613;
        font-size: 45px;
        font-weight: bold;
        border-bottom: 3px solid #E30613;
        padding-bottom: 10px;
        margin-bottom: 25px;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    </style>
    <h1 class="main-title">🔴 MONITOR COMERCIAL OCCIDENTE</h1>
    """, unsafe_allow_html=True)

def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith('.xlsx')]
    return sorted(archivos)[-1] if archivos else None

# --- LÓGICA DE CARGA DE DATOS ---
archivo_conv = buscar_archivo('Conversion')
archivo_ventas = buscar_archivo('Ventas')

# Crear pestañas con mejor diseño
tab1, tab2 = st.tabs(["📊 DESEMPEÑO CONVERSIÓN", "💰 RANKING DE VENTAS"])

with tab1:
    if archivo_conv:
        df_c = pd.read_excel(archivo_conv)
        # Limpieza de administrativos (3004, 3015)
        df_c = df_c[~df_c.iloc[:,0].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)]
        
        # Identificar columna de conversión (buscamos 'Conv' y 'Actual')
        col_conv_real = next((c for c in df_c.columns if 'Conv' in c and 'Actual' in c), df_c.columns[1])
        df_c['Conv%'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
        
        # Métricas de Semáforo
        meta = 10.9
        en_meta = df_c[df_c['Conv%'] >= meta].shape[0]
        bajo_meta = df_c[df_c['Conv%'] < meta].shape[0]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Tiendas en Meta", f"{en_meta}", "Target: 10.9%")
        m2.metric("Bajo la Meta", f"{bajo_meta}", f"-{bajo_meta}", delta_color="inverse")
        m3.metric("Promedio Zona", f"{df_c['Conv%'].mean():.2f}%")

        st.markdown("---")
        st.subheader("🏆 TOP 20 - EFICIENCIA EN TIENDA")
        
        # Mostrar tabla estilizada
        top_c = df_c[['Tienda', 'Conv%']].sort_values('Conv%', ascending=False).head(20)
        st.table(top_c.style.format({'Conv%': '{:.2f}%'}))
    else:
        st.warning("⚠️ Esperando archivo de 'Conversión' en GitHub...")

with tab2:
    if archivo_ventas:
        df_v = pd.read_excel(archivo_ventas)
        col_v = next((c for c in df_v.columns if 'Venta' in c or 'Importe' in c), None)
        col_t = next((c for c in df_v.columns if 'Tienda' in c), None)
        
        if col_v and col_t:
            st.subheader("💵 RANKING DE VENTAS ($) - TOP 20")
            top_v = df_v[[col_t, col_v]].sort_values(col_v, ascending=False).head(20)
            st.table(top_v.style.format({col_v: '${:,.2f}'}))
        else:
            st.error("❌ No se detectaron las columnas de Ventas/Importe.")
    else:
        st.info("ℹ️ Sube un reporte con la palabra 'Ventas' para activar esta sección.")

# --- PIE DE PÁGINA ---
st.markdown("<br><p style='text-align: center; color: gray;'>Gestión Estratégica Occidente | LAE José Estrada</p>", unsafe_allow_html=True)
