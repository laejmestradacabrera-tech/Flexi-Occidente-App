import streamlit as st
import pandas as pd
import os

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- ESTILO GLOBAL PROTEGIDO ---
st.markdown("""
    <style>
    .main-title {
        text-align: center; color: #E30613; font-size: 32px; font-weight: bold;
        border-bottom: 3px solid #E30613; padding-bottom: 10px; margin-bottom: 20px;
    }
    th {
        background-color: #E30613 !important; color: white !important;
        font-weight: bold !important; text-transform: uppercase !important;
        text-align: center !important; padding: 12px !important;
    }
    th.blank, tbody th {
        background-color: white !important; color: white !important;
        border: none !important; width: 1px !important;
    }
    td { text-align: center !important; font-size: 15px !important; }
    </style>
    <h1 class="main-title">🔴 MONITOR COMERCIAL OCCIDENTE</h1>
    """, unsafe_allow_html=True)

def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith('.xlsx')]
    return sorted(archivos)[-1] if archivos else None

# Recuperamos la búsqueda de ambos archivos
archivo_conv = buscar_archivo('Conversion')
archivo_modelos = buscar_archivo('Venta_Modelos')

tab1, tab2, tab3 = st.tabs(["📊 DESEMPEÑO", "👟 TOP 20 TIENDA", "🌍 TOP 20 ZONA"])

# --- PESTAÑA 1: DESEMPEÑO COMERCIAL (RECUPERADA) ---
with tab1:
    if archivo_conv:
        df_c = pd.read_excel(archivo_conv)
        df_c = df_c[~df_c.iloc[:,0].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)]
        
        col_tienda = next((c for c in df_c.columns if 'Tienda' in c or 'TIENDA' in c), df_c.columns[0])
        col_conv_real = next((c for c in df_c.columns if 'Conv' in c and 'Actual' in c), None)
        col_tkt_real = next((c for c in df_c.columns if 'Ticket' in c or 'Uds/Tkt' in c or 'Prom' in c), None)
        
        if col_conv_real and col_tkt_real:
            meta_conv, meta_tkt = 10.9, 1.29
            df_c['CONVERSIÓN'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
            df_c['TICKET PROMEDIO'] = df_c[col_tkt_real]
            
            def color_semaforo(row):
                c_conv = row['CONVERSIÓN'] >= meta_conv
                c_tkt = row['TICKET PROMEDIO'] >= meta_tkt
                if c_conv and c_tkt: return ['background-color: #d4edda; color: #155724'] * 3
                elif c_conv or c_tkt: return ['background-color: #fff3cd; color: #856404'] * 3
                else: return ['background-color: #f8d7da; color: #721c24'] * 3

            ranking = df_c[[col_tienda, 'CONVERSIÓN', 'TICKET PROMEDIO']].sort_values(by='CONVERSIÓN', ascending=False)
            ranking.columns = ['TIENDA', 'CONVERSIÓN', 'TICKET PROMEDIO']
            st.table(ranking.style.apply(color_semaforo, axis=1).format({'CONVERSIÓN': '{:.2f}%', 'TICKET PROMEDIO': '{:.2f}'}))
    else:
        st.info("ℹ️ Esperando archivo de Conversión...")

# --- PROCESAMIENTO PARA TOP 20 (TIENDA Y ZONA) ---
if archivo_modelos:
    df_m = pd.read_excel(archivo_modelos)
    
    # Identificación de columnas
    col_m = next((c for c in df_m.columns if c.lower() in ['clave', 'modelo', 'estilo']), df_m.columns[1])
    col_p = next((c for c in df_m.columns if c.lower() in ['pares', 'cantidad', 'venta']), df_m.columns[2])
    col_t = next((c for c in df_m.columns if c.lower() in ['tienda', 'sucursal']), df_m.columns[0])
    
    def resaltar_top_5(data):
        estilo = pd.DataFrame('', index=data.index, columns=data.columns)
        estilo.iloc[0:5, :] = 'background-color: #d1e7dd; color: #0f5132; font-weight: bold'
        return estilo

    with tab2:
        tiendas = sorted(df_m[col_t].unique())
        t_sel = st.selectbox("Selecciona Tienda:", tiendas)
        df_t = df_m[df_m[col_t] == t_sel].groupby(col_m)[col_p].sum().reset_index()
        top_t = df_t.sort_values(by=col_p, ascending=False).head(20).reset_index(drop=True)
        top_t.columns = ['MODELO', 'PARES VENDIDOS']
        st.table(top_t.style.apply(resaltar_top_5, axis=None))

    with tab3:
        st.subheader("🌍 Consolidado Zona Occidente")
        df_z = df_m.groupby(col_m)[col_p].sum().reset_index()
        top_z = df_z.sort_values(by=col_p, ascending=False).head(20).reset_index(drop=True)
        top_z.columns = ['MODELO', 'PARES VENDIDOS']
        st.table(top_z.style.apply(resaltar_top_5, axis=None))
else:
    with tab2: st.info("ℹ️ Esperando archivo Venta_Modelos.xlsx...")
    with tab3: st.info("ℹ️ Esperando archivo Venta_Modelos.xlsx...")

st.markdown("<p style='text-align: center; color: gray; font-size: 10px;'>Gestión Occidente | José Estrada</p>", unsafe_allow_html=True)
