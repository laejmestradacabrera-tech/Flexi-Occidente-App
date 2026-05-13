import streamlit as st
import pandas as pd
import os

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- ESTILO GLOBAL ---
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

archivo_modelos = buscar_archivo('Ventas')

# Agregamos la nueva pestaña para el Top por Zona
tab1, tab2, tab3 = st.tabs(["📊 DESEMPEÑO", "👟 TOP 20 TIENDA", "🌍 TOP 20 ZONA"])

# --- PROCESAMIENTO DE DATOS COMÚN ---
if archivo_modelos:
    df_m = pd.read_excel(archivo_modelos)
    # Limpieza estándar: Solo calzado (evitar accesorios de proveedores 415, 426, 427)
    if 'Provee.' in df_m.columns:
        df_m = df_m[~df_m['Provee.'].astype(str).isin(['415', '426', '427'])]
    
    col_mod = 'clave' if 'clave' in df_m.columns else df_m.columns[1]
    col_cant = 'Pares' if 'Pares' in df_m.columns else df_m.columns[2]
    col_tienda = 'Tienda' if 'Tienda' in df_m.columns else df_m.columns[0]

    # --- PESTAÑA 2: TOP 20 POR TIENDA (EXISTENTE) ---
    with tab2:
        tiendas_disponibles = sorted(df_m[col_tienda].unique())
        tienda_sel = st.selectbox("Selecciona Tienda para ver su Top:", tiendas_disponibles)
        
        df_tienda = df_m[df_m[col_tienda] == tienda_sel]
        top_tienda = df_tienda.groupby(col_mod)[col_cant].sum().reset_index()
        top_tienda = top_tienda.sort_values(by=col_cant, ascending=False).head(20).reset_index(drop=True)
        top_tienda.columns = ['MODELO', 'PARES VENDIDOS']

        def resaltar_top_5(data):
            estilo = pd.DataFrame('', index=data.index, columns=data.columns)
            estilo.iloc[0:5, :] = 'background-color: #d1e7dd; color: #0f5132; font-weight: bold'
            return estilo

        st.subheader(f"🏆 Ranking de Ventas - Tienda {tienda_sel}")
        st.table(top_tienda.style.apply(resaltar_top_5, axis=None))

    # --- PESTAÑA 3: TOP 20 POR ZONA (NUEVA) ---
    with tab3:
        st.subheader("🌍 Consolidado Zona Occidente (21 Tiendas)")
        
        # Agrupamos por modelo sin importar la tienda
        top_zona = df_m.groupby(col_mod)[col_cant].sum().reset_index()
        top_zona = top_zona.sort_values(by=col_cant, ascending=False).head(20).reset_index(drop=True)
        top_zona.columns = ['MODELO', 'PARES VENDIDOS']

        st.table(top_zona.style.apply(resaltar_top_5, axis=None))

else:
    st.info("ℹ️ Carga el archivo de ventas por operación para activar los rankings.")

st.markdown("<p style='text-align: center; color: gray; font-size: 10px;'>Gestión Occidente | José Estrada</p>", unsafe_allow_html=True)
