import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- ESTILO ROJO FLEXI Y SEMÁFORO ---
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
        font-size: 14px;
    }
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
    <h1 class="main-title">🔴 MONITOR COMERCIAL OCCIDENTE</h1>
    """, unsafe_allow_html=True)

def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith('.xlsx')]
    return sorted(archivos)[-1] if archivos else None

archivo_conv = buscar_archivo('Conversion')

if archivo_conv:
    df_c = pd.read_excel(archivo_conv)
    df_c = df_c[~df_c.iloc[:,0].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)]
    
    col_tienda = next((c for c in df_c.columns if 'Tienda' in c or 'TIENDA' in c), df_c.columns[0])
    col_conv_real = next((c for c in df_c.columns if 'Conv' in c and 'Actual' in c), None)
    col_tkt_real = next((c for c in df_c.columns if 'Ticket' in c or 'Uds/Tkt' in c or 'Prom' in c), None)
    
    if col_conv_real and col_tkt_real:
        # Metas
        meta_conv, meta_tkt = 10.9, 1.29
        
        # Datos base
        df_c['Conversión'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
        df_c['Ticket Promedio'] = df_c[col_tkt_real]
        
        # --- CÁLCULO DE BRECHAS (PUNTO EXTRA) ---
        def calc_brecha_conv(val):
            diff = val - meta_conv
            return "✅" if diff >= 0 else f"{diff:.2f}%"

        def calc_brecha_tkt(val):
            diff = val - meta_tkt
            return "✅" if diff >= 0 else f"{diff:.2f}"

        df_c['Faltante Conv.'] = df_c['Conversión'].apply(calc_brecha_conv)
        df_c['Faltante Tkt.'] = df_c['Ticket Promedio'].apply(calc_brecha_tkt)

        # Semáforo
        def aplicar_color(row):
            c_conv = row['Conversión'] >= meta_conv
            c_tkt = row['Ticket Promedio'] >= meta_tkt
            if c_conv and c_tkt: return ['background-color: #d4edda; color: #155724'] * 5
            elif c_conv or c_tkt: return ['background-color: #fff3cd; color: #856404'] * 5
            else: return ['background-color: #f8d7da; color: #721c24'] * 5

        # Métricas principales
        m1, m2, m3 = st.columns(3)
        m1.metric("Zona Conv.", f"{df_c['Conversión'].mean():.2f}%", f"Meta: {meta_conv}%")
        m2.metric("Zona Tkt.", f"{df_c['Ticket Promedio'].mean():.2f}", f"Meta: {meta_tkt}")
        m3.metric("Excelencia", f"{df_c[(df_c['Conversión']>=meta_conv) & (df_c['Ticket Promedio']>=meta_tkt)].shape[0]}")

        st.markdown("---")
        
        # Ordenar y Tabla Final
        df_c['Prioridad'] = df_c.apply(lambda r: 2 if (r['Conversión'] >= meta_conv and r['Ticket Promedio'] >= meta_tkt) 
                                     else (1 if (r['Conversión'] >= meta_conv or r['Ticket Promedio'] >= meta_tkt) else 0), axis=1)
        
        ranking = df_c.sort_values(by=['Prioridad', 'Conversión'], ascending=[False, False])
        tabla_final = ranking[[col_tienda, 'Conversión', 'Faltante Conv.', 'Ticket Promedio', 'Faltante Tkt.']]
        tabla_final.columns = ['Tienda', 'Conversión', 'Faltante Conv.', 'Ticket Promedio', 'Faltante Tkt.']
        
        st.table(tabla_final.style.apply(aplicar_color, axis=1).format({
            'Conversión': '{:.2f}%',
            'Ticket Promedio': '{:.2f}'
        }))
        
        st.caption(f"🎯 Metas de la Zona: Conversión {meta_conv}% | Ticket Promedio {meta_tkt}")
        
    else:
        st.error("❌ Columnas no encontradas.")
else:
    st.warning("⚠️ Sube el archivo de 'Conversion' a GitHub.")

st.markdown("<p style='text-align: center; color: gray;'>Gestión Estratégica Occidente | LAE José Estrada</p>", unsafe_allow_html=True)
