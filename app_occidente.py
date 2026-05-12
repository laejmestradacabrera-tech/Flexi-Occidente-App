import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- ESTILO ROJO FLEXI ---
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #E30613;
        font-size: 40px;
        font-weight: bold;
        border-bottom: 3px solid #E30613;
        padding-bottom: 10px;
    }
    .stTable thead tr th {
        background-color: #E30613 !important;
        color: white !important;
        text-align: center !important;
        font-weight: bold !important;
    }
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
    <h1 class="main-title">🔴 MONITOR COMERCIAL OCCIDENTE</h1>
    """, unsafe_allow_html=True)

def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith('.xlsx')]
    return sorted(archivos)[-1] if archivos else None

# --- CARGA DE DATOS ---
archivo_conv = buscar_archivo('Conversion')
archivo_modelos = buscar_archivo('Modelos')

tab1, tab2 = st.tabs(["📊 DESEMPEÑO COMERCIAL", "👟 TOP 20 MODELOS"])

with tab1:
    if archivo_conv:
        df_c = pd.read_excel(archivo_conv)
        # FILTRO CRÍTICO: Eliminamos 3015 y otros administrativos
        df_c = df_c[~df_c.iloc[:,0].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)]
        
        col_tienda = next((c for c in df_c.columns if 'Tienda' in c or 'TIENDA' in c), df_c.columns[0])
        col_conv_real = next((c for c in df_c.columns if 'Conv' in c and 'Actual' in c), None)
        col_tkt_real = next((c for c in df_c.columns if 'Ticket' in c or 'Uds/Tkt' in c or 'Prom' in c), None)
        
        if col_conv_real and col_tkt_real:
            meta_conv, meta_tkt = 10.9, 1.29
            df_c['Conversión'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
            df_c['Ticket Promedio'] = df_c[col_tkt_real]
            
            df_c['Faltante Conv.'] = df_c['Conversión'].apply(lambda x: "✅" if x >= meta_conv else f"{x - meta_conv:.2f}%")
            df_c['Faltante Tkt.'] = df_c['Ticket Promedio'].apply(lambda x: "✅" if x >= meta_tkt else f"{x - meta_tkt:.2f}")

            def aplicar_color(row):
                c_conv, c_tkt = row['Conversión'] >= meta_conv, row['Ticket Promedio'] >= meta_tkt
                if c_conv and c_tkt: return ['background-color: #d4edda; color: #155724'] * 5
                elif c_conv or c_tkt: return ['background-color: #fff3cd; color: #856404'] * 5
                else: return ['background-color: #f8d7da; color: #721c24'] * 5

            m1, m2, m3 = st.columns(3)
            m1.metric("Zona Conv.", f"{df_c['Conversión'].mean():.2f}%", f"Meta: {meta_conv}%")
            m2.metric("Zona Tkt.", f"{df_c['Ticket Promedio'].mean():.2f}", f"Meta: {meta_tkt}")
            m3.metric("Excelencia", f"{df_c[(df_c['Conversión']>=meta_conv) & (df_c['Ticket Promedio']>=meta_tkt)].shape[0]}")

            st.markdown("---")
            df_c['Prioridad'] = df_c.apply(lambda r: 2 if (r['Conversión'] >= meta_conv and r['Ticket Promedio'] >= meta_tkt) else (1 if (r['Conversión'] >= meta_conv or r['Ticket Promedio'] >= meta_tkt) else 0), axis=1)
            ranking = df_c.sort_values(by=['Prioridad', 'Conversión'], ascending=[False, False])
            tabla_final = ranking[[col_tienda, 'Conversión', 'Faltante Conv.', 'Ticket Promedio', 'Faltante Tkt.']]
            tabla_final.columns = ['Tienda', 'Conversión', 'Faltante Conv.', 'Ticket Promedio', 'Faltante Tkt.']
            
            st.table(tabla_final.style.apply(aplicar_color, axis=1).format({'Conversión': '{:.2f}%', 'Ticket Promedio': '{:.2f}'}))
        else: st.error("❌ Columnas no detectadas.")

with tab2:
    if archivo_modelos:
        df_m = pd.read_excel(archivo_modelos)
        
        # --- FILTROS DE CALZADO Y TIENDAS ---
        col_t = next((c for c in df_m.columns if 'Tienda' in c or 'TIENDA' in c), df_m.columns[0])
        
        # 1. Eliminar Tienda 3015 y otras administrativas del Ranking
        df_m = df_m[~df_m[col_t].astype(str).str.contains('3004|3015', na=False)]
        
        # 2. Eliminar proveedores 415, 426 y 427
        col_prov = next((c for c in df_m.columns if 'Prov' in c or 'PROV' in c), None)
        if col_prov:
            df_m = df_m[~df_m[col_prov].astype(str).isin(['415', '426', '427'])]
            
        # 3. Eliminar modelo AUBOLPETT0RO
        col_mod = next((c for c in df_m.columns if 'Modelo' in c or 'Estilo' in c or 'Art' in c), df_m.columns[1])
        df_m = df_m[df_m[col_mod].astype(str) != 'AUBOLPETT0RO']
        
        # --- LÓGICA DE VISUALIZACIÓN ---
        tiendas = sorted(df_m[col_t].unique())
        tienda_sel = st.selectbox("Selecciona Tienda para ver el Top de Modelos:", tiendas)
        
        df_t = df_m[df_m[col_t] == tienda_sel].copy()
        col_cant = next((c for c in df_t.columns if 'Cant' in c or 'Pares' in c or 'Venta' in c), df_t.columns[2])
        
        top_20 = df_t[[col_mod, col_cant]].sort_values(by=col_cant, ascending=False).head(20)
        top_20.columns = ['Modelo / Estilo', 'Pares Vendidos']
        
        st.subheader(f"👟 Top 20 Calzado más vendido - Tienda {tienda_sel}")
        st.table(top_20)
        st.caption("Nota: Reporte filtrado por calzado estratégico. Se excluyó la tienda 3015.")
    else:
        st.info("ℹ️ Sube un archivo con la palabra 'Modelos' en GitHub.")

st.markdown("<p style='text-align: center; color: gray;'>Gestión Estratégica Occidente | LAE José Estrada</p>", unsafe_allow_html=True)
