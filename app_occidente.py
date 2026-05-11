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
        # Preparamos los datos
        df_c['Conversión'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
        df_c['Ticket Promedio'] = df_c[col_tkt_real]
        
        meta_conv, meta_tkt = 10.9, 1.29

        # --- LÓGICA DEL SEMÁFORO CORREGIDA ---
        def aplicar_color(row):
            # Ahora usamos los nombres exactos que tiene la tabla final
            c_conv = row['Conversión'] >= meta_conv
            c_tkt = row['Ticket Promedio'] >= meta_tkt
            
            if c_conv and c_tkt:
                return ['background-color: #d4edda; color: #155724'] * 3  # Verde
            elif c_conv or c_tkt:
                return ['background-color: #fff3cd; color: #856404'] * 3  # Amarillo
            else:
                return ['background-color: #f8d7da; color: #721c24'] * 3  # Rojo

        # Métricas principales
        excelencia = df_c[(df_c['Conversión'] >= meta_conv) & (df_c['Ticket Promedio'] >= meta_tkt)].shape[0]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Promedio Zona Conv.", f"{df_c['Conversión'].mean():.2f}%")
        m2.metric("Promedio Zona Tkt.", f"{df_c['Ticket Promedio'].mean():.2f}")
        m3.metric("Tiendas en Excelencia", f"{excelencia}")

        st.markdown("---")
        
        # Ordenar por cumplimiento
        df_c['Prioridad'] = df_c.apply(lambda r: 2 if (r['Conversión'] >= meta_conv and r['Ticket Promedio'] >= meta_tkt) 
                                     else (1 if (r['Conversión'] >= meta_conv or r['Ticket Promedio'] >= meta_tkt) else 0), axis=1)
        
        ranking = df_c.sort_values(by=['Prioridad', 'Conversión'], ascending=[False, False])
        
        # Tabla Final
        tabla_final = ranking[[col_tienda, 'Conversión', 'Ticket Promedio']]
        tabla_final.columns = ['Tienda', 'Conversión', 'Ticket Promedio']
        
        st.table(tabla_final.style.apply(aplicar_color, axis=1).format({
            'Conversión': '{:.2f}%',
            'Ticket Promedio': '{:.2f}'
        }))
        
        st.caption("🟢 Verde: Cumple ambos | 🟡 Amarillo: Cumple uno | 🔴 Rojo: No cumple ninguno")
        
    else:
        st.error("❌ No se detectaron las columnas de datos correctamente.")
else:
    st.warning("⚠️ Sube el archivo de 'Conversion' a GitHub.")

st.markdown("<p style='text-align: center; color: gray;'>Gestión Estratégica Occidente | LAE José Estrada</p>", unsafe_allow_html=True)
