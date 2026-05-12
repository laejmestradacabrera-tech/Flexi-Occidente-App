import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- ESTILO GENERAL ROJO FLEXI ---
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #E30613;
        font-size: 35px;
        font-weight: bold;
        border-bottom: 3px solid #E30613;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    /* Diseño de celdas: compacto y centrado */
    .stTable td, .stTable th {
        max-width: 100px !important;
        padding: 6px !important;
        text-align: center !important;
        font-size: 14px !important;
    }
    /* ENCABEZADOS: FONDO ROJO Y LETRAS BLANCAS PARA TODO EL MONITOR */
    .stTable thead tr th {
        background-color: #E30613 !important;
        color: white !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
    }
    /* Ocultar el índice automático de Python */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
    <h1 class="main-title">MONITOR COMERCIAL OCCIDENTE</h1>
    """, unsafe_allow_html=True)

def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith('.xlsx')]
    return sorted(archivos)[-1] if archivos else None

archivo_conv = buscar_archivo('Conversion')
archivo_modelos = buscar_archivo('Modelos')

tab1, tab2 = st.tabs(["📊 DESEMPEÑO COMERCIAL", "👟 TOP 20 MODELOS"])

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

            def aplicar_color_semaforo(row):
                c_conv, c_tkt = row['CONVERSIÓN'] >= meta_conv, row['TICKET PROMEDIO'] >= meta_tkt
                if c_conv and c_tkt: return ['background-color: #d4edda; color: #155724'] * 5
                elif c_conv or c_tkt: return ['background-color: #fff3cd; color: #856404'] * 5
                else: return ['background-color: #f8d7da; color: #721c24'] * 5

            st.markdown("---")
            ranking = df_c.sort_values(by=['CONVERSIÓN'], ascending=False)
            tabla_final = ranking[[col_tienda, 'CONVERSIÓN', 'FALTANTE CONV.', 'TICKET PROMEDIO', 'FALTANTE TKT.']]
            tabla_final.columns = ['TIENDA', 'CONVERSIÓN', 'FALTANTE CONV.', 'TICKET PROMEDIO', 'FALTANTE TKT.']
            st.table(tabla_final.style.apply(aplicar_color_semaforo, axis=1).format({'CONVERSIÓN': '{:.2f}%', 'TICKET PROMEDIO': '{:.2f}'}))

with tab2:
    if archivo_modelos:
        df_m = pd.read_excel(archivo_modelos)
        col_t = next((c for c in df_m.columns if 'Tienda' in c or 'TIENDA' in c), df_m.columns[0])
        col_mod = next((c for c in df_m.columns if 'Modelo' in c or 'Estilo' in c or 'Art' in c), df_m.columns[1])
        col_cant = next((c for c in df_m.columns if 'Cant' in c or 'Pares' in c or 'Venta' in c), df_m.columns[2])
        
        df_agrupado = df_m.groupby([col_t, col_mod])[col_cant].sum().reset_index()
        tienda_sel = st.selectbox("Selecciona Tienda para el Ranking:", sorted(df_agrupado[col_t].unique()))
        
        df_tienda = df_agrupado[df_agrupado[col_t] == tienda_sel].copy()
        top_20 = df_tienda[[col_mod, col_cant]].sort_values(by=col_cant, ascending=False).head(20).reset_index(drop=True)
        
        # --- ENCABEZADOS SOLICITADOS ---
        top_20.columns = ['MODELO', 'PARES'] 
        
        def resaltar_top_5_solo_modelo(data):
            estilos = pd.DataFrame('', index=data.index, columns=data.columns)
            estilos.iloc[0:5, 0] = 'background-color: #d1e7dd; color: #0f5132; font-weight: bold'
            return estilos

        st.subheader(f"🏆 TOP 20 VENTAS - TIENDA {tienda_sel}")
        # La tabla usará el estilo general de encabezados rojos definido arriba
        st.table(top_20.style.apply(resaltar_top_5_solo_modelo, axis=None))
    else:
        st.info("ℹ️ Sube el archivo 'Modelos' en GitHub.")

st.markdown("<p style='text-align: center; color: gray;'>Gestión Estratégica Occidente | LAE José Estrada</p>", unsafe_allow_html=True)
