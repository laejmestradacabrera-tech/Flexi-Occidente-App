import streamlit as st
import pandas as pd
import os

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

st.markdown("<h1 style='text-align: center; color: #E30613;'>🔴 MONITOR COMERCIAL OCCIDENTE</h1>", unsafe_allow_html=True)

# 2. FUNCIÓN PARA BUSCAR ARCHIVOS
def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith('.xlsx')]
    return sorted(archivos)[-1] if archivos else None

archivo_conv = buscar_archivo('Conversion')
archivo_modelos = buscar_archivo('Modelos')

tab1, tab2 = st.tabs(["📊 DESEMPEÑO COMERCIAL", "👟 TOP 20 MODELOS"])

# --- PESTAÑA 1: DESEMPEÑO (ESTABLE) ---
with tab1:
    if archivo_conv:
        df_c = pd.read_excel(archivo_conv)
        df_c = df_c[~df_c.iloc[:,0].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)]
        col_tienda = next((c for c in df_c.columns if 'Tienda' in c or 'TIENDA' in c), df_c.columns[0])
        col_conv_real = next((c for c in df_c.columns if 'Conv' in c and 'Actual' in c), None)
        col_tkt_real = next((c for c in df_c.columns if 'Ticket' in c or 'Uds/Tkt' in c or 'Prom' in c), None)
        
        if col_conv_real and col_tkt_real:
            df_c['CONVERSIÓN'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
            df_c['TICKET PROMEDIO'] = df_c[col_tkt_real]
            ranking = df_c[[col_tienda, 'CONVERSIÓN', 'TICKET PROMEDIO']].sort_values(by='CONVERSIÓN', ascending=False)
            ranking.columns = ['TIENDA', 'CONVERSIÓN', 'TICKET PROMEDIO']
            st.table(ranking.head(21))

# --- PESTAÑA 2: SUBIR TOP 20 (NOMBRES DE COLUMNA) ---
with tab2:
    if archivo_modelos:
        df_m = pd.read_excel(archivo_modelos)
        
        # Identificar columnas originales
        col_t = next((c for c in df_m.columns if 'Tienda' in c or 'TIENDA' in c), df_m.columns[0])
        col_mod = next((c for c in df_m.columns if 'Modelo' in c or 'Estilo' in c or 'Art' in c), df_m.columns[1])
        col_cant = next((c for c in df_m.columns if 'Cant' in c or 'Pares' in c or 'Venta' in c), df_m.columns[2])
        col_prov = next((c for c in df_m.columns if 'Prov' in c or 'PROV' in c), None)

        # Filtros básicos (Solo calzado)
        if col_prov:
            df_m = df_m[~df_m[col_prov].astype(str).isin(['415', '426', '427'])]
        df_m = df_m[~df_m[col_t].astype(str).str.contains('3004|3015', na=False)]

        df_agrupado = df_m.groupby([col_t, col_mod])[col_cant].sum().reset_index()
        tienda_sel = st.selectbox("Selecciona Tienda:", sorted(df_agrupado[col_t].unique()))
        
        df_tienda = df_agrupado[df_agrupado[col_t] == tienda_sel].copy()
        
        # Preparar solo las 2 columnas deseadas
        top_20 = df_tienda[[col_mod, col_cant]].sort_values(by=col_cant, ascending=False).head(20).reset_index(drop=True)
        
        # CAMBIO DE NOMBRES SOLICITADO
        top_20.columns = ['MODELO', 'PARES VENDIDOS'] 

        st.subheader(f"Ranking de Ventas - {tienda_sel}")
        st.table(top_20) # Tabla simple sin colores aún
    else:
        st.info("ℹ️ Esperando archivo de modelos...")

st.markdown("<p style='text-align: center; color: gray; font-size: 10px;'>Gestión Occidente | José Estrada</p>", unsafe_allow_html=True)
