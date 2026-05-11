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

tab1, tab2 = st.tabs(["📊 DESEMPEÑO COMERCIAL", "💰 RANKING DE VENTAS"])

with tab1:
    if archivo_conv:
        df_c = pd.read_excel(archivo_conv)
        # Limpieza de administrativos
        df_c = df_c[~df_c.iloc[:,0].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)]
        
        # Identificar columnas: Conversión y Ticket Promedio
        col_conv_real = next((c for c in df_c.columns if 'Conv' in c and 'Actual' in c), None)
        col_tkt_real = next((c for c in df_c.columns if 'Ticket' in c or 'Uds/Tkt' in c or 'Prom' in c), None)
        
        if col_conv_real and col_tkt_real:
            df_c['Conv%'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
            df_c['Ticket_Prom'] = df_c[col_tkt_real]
            
            # Métricas superiores
            meta_conv = 10.9
            meta_tkt = 1.29
            prom_zona_conv = df_c['Conv%'].mean()
            prom_zona_tkt = df_c['Ticket_Prom'].mean()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Promedio Conversión", f"{prom_zona_conv:.2f}%", f"Meta: {meta_conv}%")
            m2.metric("Promedio Ticket", f"{prom_zona_tkt:.2f}", f"Meta: {meta_tkt}")
            m3.metric("Tiendas Analizadas", f"{len(df_c)}")

            st.markdown("---")
            st.subheader("🏆 RANKING OPERATIVO (TOP 20)")
            
            # Tabla con los dos decimales solicitados
            ranking = df_c[['Tienda', 'Conv%', 'Ticket_Prom']].sort_values('Conv%', ascending=False).head(20)
            st.table(ranking.style.format({
                'Conv%': '{:.2f}%',
                'Ticket_Prom': '{:.2f}'
            }))
        else:
            st.error("❌ No encontré las columnas de 'Conversión' o 'Ticket Promedio' en el Excel.")
    else:
        st.warning("⚠️ Sube el archivo de 'Conversión' a GitHub.")

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
        st.info("ℹ️ Sube un reporte con la palabra 'Ventas' para activar esta sección.")

st.markdown("<br><p style='text-align: center; color: gray;'>Gestión Estratégica Occidente | LAE José Estrada</p>", unsafe_allow_html=True)
