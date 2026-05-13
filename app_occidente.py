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

def buscar_archivo_exacto():
    # Buscamos específicamente el nombre que me indicaste
    if os.path.exists('Venta_Modelos.xlsx'):
        return 'Venta_Modelos.xlsx'
    # Si no, buscamos cualquier archivo que contenga "Venta" y sea Excel
    archivos = [f for f in os.listdir('.') if 'venta' in f.lower() and f.endswith('.xlsx')]
    return sorted(archivos)[-1] if archivos else None

archivo_ventas = buscar_archivo_exacto()

tab1, tab2, tab3 = st.tabs(["📊 DESEMPEÑO", "👟 TOP 20 TIENDA", "🌍 TOP 20 ZONA"])

if archivo_ventas:
    try:
        df_m = pd.read_excel(archivo_ventas)
        
        # IDENTIFICACIÓN DINÁMICA DE COLUMNAS (Ajustada a tu archivo)
        col_mod = next((c for c in df_m.columns if c.lower() in ['clave', 'modelo', 'estilo', 'artículo']), df_m.columns[1])
        col_cant = next((c for c in df_m.columns if c.lower() in ['pares', 'cantidad', 'venta', 'unidades']), df_m.columns[2])
        col_tienda = next((c for c in df_m.columns if c.lower() in ['tienda', 'sucursal', 'nombre']), df_m.columns[0])
        col_prov = next((c for c in df_m.columns if 'prov' in c.lower() or 'provee' in c.lower()), None)

        # Limpieza de accesorios (Proveedores 415, 426, 427)
        if col_prov:
            df_m = df_m[~df_m[col_prov].astype(str).isin(['415', '426', '427'])]
        
        # Filtro de tiendas que no son de venta al público
        df_m = df_m[~df_m[col_tienda].astype(str).str.contains('3004|3015', na=False)]

        def resaltar_top_5(data):
            estilo = pd.DataFrame('', index=data.index, columns=data.columns)
            estilo.iloc[0:5, :] = 'background-color: #d1e7dd; color: #0f5132; font-weight: bold'
            return estilo

        # --- PESTAÑA 2: TOP 20 POR TIENDA ---
        with tab2:
            tiendas_disponibles = sorted(df_m[col_tienda].unique())
            tienda_sel = st.selectbox("Selecciona Tienda para ver su Ranking:", tiendas_disponibles)
            
            df_tienda = df_m[df_m[col_tienda] == tienda_sel]
            top_tienda = df_tienda.groupby(col_mod)[col_cant].sum().reset_index()
            top_tienda = top_tienda.sort_values(by=col_cant, ascending=False).head(20).reset_index(drop=True)
            top_tienda.columns = ['MODELO', 'PARES VENDIDOS']
            st.table(top_tienda.style.apply(resaltar_top_5, axis=None))

        # --- PESTAÑA 3: TOP 20 POR ZONA (CONSOLIDADO) ---
        with tab3:
            st.subheader("🌍 Consolidado Zona Occidente (21 Tiendas)")
            # Aquí agrupamos por modelo sumando las ventas de todas las tiendas
            top_zona = df_m.groupby(col_mod)[col_cant].sum().reset_index()
            top_zona = top_zona.sort_values(by=col_cant, ascending=False).head(20).reset_index(drop=True)
            top_zona.columns = ['MODELO', 'PARES VENDIDOS']
            st.table(top_zona.style.apply(resaltar_top_5, axis=None))
            
    except Exception as e:
        st.error(f"Error al procesar el archivo '{archivo_ventas}': {e}")
else:
    st.info(f"ℹ️ El archivo 'Venta_Modelos.xlsx' no se encuentra en el repositorio.")

st.markdown("<p style='text-align: center; color: gray; font-size: 10px;'>Gestión Occidente | José Estrada</p>", unsafe_allow_html=True)
