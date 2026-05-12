import streamlit as st
import pandas as pd
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- 2. ESTILO "FIXED-WIDTH" (CORRIGE EL ERROR DE COLUMNAS REDUCIDAS) ---
st.markdown("""
    <style>
    .main-title {
        text-align: center; color: #E30613; font-size: 32px; font-weight: bold;
        border-bottom: 3px solid #E30613; padding-bottom: 10px; margin-bottom: 20px;
    }
    /* FUERZA ENCABEZADOS ROJOS CON ANCHO FIJO */
    th {
        background-color: #E30613 !important;
        color: white !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        text-align: center !important;
        padding: 10px !important;
        min-width: 150px !important; /* Evita que el nombre desaparezca al reducir */
    }
    td { 
        text-align: center !important; 
        font-size: 14px !important; 
        padding: 8px !important;
    }
    /* OCULTAR ÍNDICE (ELIMINA EL DESPLAZAMIENTO HACIA LA DERECHA) */
    thead tr th:first-child { display: none !important; }
    tbody th { display: none !important; }
    </style>
    <h1 class="main-title">🔴 MONITOR COMERCIAL OCCIDENTE</h1>
    """, unsafe_allow_html=True)

def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith('.xlsx')]
    return sorted(archivos)[-1] if archivos else None

archivo_conv = buscar_archivo('Conversion')
archivo_modelos = buscar_archivo('Modelos')

tab1, tab2 = st.tabs(["📊 DESEMPEÑO COMERCIAL", "👟 TOP 20 MODELOS"])

# --- TAB 1: DESEMPEÑO ---
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
            df_c['FALTANTE CONV.'] = df_c['CONVERSIÓN'].apply(lambda x: "✅" if x >= meta_conv else f"{x - meta_conv:.2f}%")
            df_c['FALTANTE TKT.'] = df_c['TICKET PROMEDIO'].apply(lambda x: "✅" if x >= meta_tkt else f"{x - meta_tkt:.2f}")

            def color_desempeno(row):
                c_conv, c_tkt = row['CONVERSIÓN'] >= meta_conv, row['TICKET PROMEDIO'] >= meta_tkt
                if c_conv and c_tkt: return ['background-color: #d4edda; color: #155724'] * 5
                elif c_conv or c_tkt: return ['background-color: #fff3cd; color: #856404'] * 5
                else: return ['background-color: #f8d7da; color: #721c24'] * 5

            ranking = df_c[[col_tienda, 'CONVERSIÓN', 'FALTANTE CONV.', 'TICKET PROMEDIO', 'FALTANTE TKT.']].sort_values(by='CONVERSIÓN', ascending=False)
            ranking.columns = ['TIENDA', 'CONVERSIÓN', 'FALTANTE CONV.', 'TICKET PROMEDIO', 'FALTANTE TKT.']
            st.table(ranking.style.apply(color_desempeno, axis=1).format({'CONVERSIÓN': '{:.2f}%', 'TICKET PROMEDIO': '{:.2f}'}))

# --- TAB 2: TOP 20 ---
with tab2:
    if archivo_modelos:
        df_m = pd.read_excel(archivo_modelos)
        col_t = next((c for c in df_m.columns if 'Tienda' in c or 'TIENDA' in c), df_m.columns[0])
        col_mod = next((c for c in df_m.columns if 'Modelo' in c or 'Estilo' in c or 'Art' in c), df_m.columns[1])
        col_cant = next((c for c in df_m.columns if 'Cant' in c or 'Pares' in c or 'Venta' in c), df_m.columns[2])
        col_prov = next((c for c in df_m.columns if 'Prov' in c or 'PROV' in c), None)

        if col_prov:
            df_m = df_m[~df_m[col_prov].astype(str).isin(['415', '426', '427'])]
        df_m = df_m[df_m[col_mod].astype(str) != 'AUBOLPETT0RO']
        df_m = df_m[~df_m[col_t].astype(str).str.contains('3004|3015', na=False)]

        df_agrupado = df_m.groupby([col_t, col_mod])[col_cant].sum().reset_index()
        tienda_sel = st.selectbox("Tienda:", sorted(df_agrupado[col_t].unique()))
        
        df_tienda = df_agrupado[df_agrupado[col_t] == tienda_sel].copy()
        
        # RESET INDEX ES VITAL: Convierte el Modelo en columna real para que el CSS lo vea
        top_20 = df_tienda[[col_mod, col_cant]].sort_values(by=col_cant, ascending=False).head(20).reset_index(drop=True)
        
        # NOMBRES EXACTOS
        top_20.columns = ['MODELO', 'PARES VENDIDOS'] 

        def resaltar_filas_top_5(data):
            estilo = pd.DataFrame('', index=data.index, columns=data.columns)
            estilo.iloc[0:5, :] = 'background-color: #d1e7dd; color: #0f5132; font-weight: bold'
            return estilo

        st.subheader(f"🏆 RANKING DE VENTAS - TIENDA {tienda_sel}")
        # USAMOS st.table() que es más estable para estilos CSS fijos
        st.table(top_20.style.apply(resaltar_filas_top_5, axis=None))

st.markdown("<p style='text-align: center; color: gray; font-size: 10px;'>Gestión Occidente | LAE José Estrada</p>", unsafe_allow_html=True)
