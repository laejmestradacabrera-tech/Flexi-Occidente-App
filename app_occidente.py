import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- ESTILO ROJO FLEXI, TABLA SIN ÍNDICE Y ENCABEZADOS RESALTADOS ---
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
    /* Estilo para resaltar encabezados de la tabla */
    .stTable thead tr th {
        background-color: #E30613 !important;
        color: white !important;
        text-align: center !important;
        font-weight: bold !important;
    }
    /* Eliminar la numeración de la izquierda */
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
    # Limpieza: quitamos administrativos y totales
    df_c = df_c[~df_c.iloc[:,0].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)]
    
    # Identificar columnas
    col_tienda = next((c for c in df_c.columns if 'Tienda' in c or 'TIENDA' in c), df_c.columns[0])
    col_conv_real = next((c for c in df_c.columns if 'Conv' in c and 'Actual' in c), None)
    col_tkt_real = next((c for c in df_c.columns if 'Ticket' in c or 'Uds/Tkt' in c or 'Prom' in c), None)
    
    if col_conv_real and col_tkt_real:
        df_c['Conv%'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
        df_c['Ticket_Prom'] = df_c[col_tkt_real]
        
        # Lógica de Metas
        meta_conv, meta_tkt = 10.9, 1.29
        df_c['Cumple'] = (df_c['Conv%'] >= meta_conv) & (df_c['Ticket_Prom'] >= meta_tkt)
        
        # Métricas principales
        m1, m2, m3 = st.columns(3)
        m1.metric("Promedio Zona Conv.", f"{df_c['Conv%'].mean():.2f}%")
        m2.metric("Promedio Zona Tkt.", f"{df_c['Ticket_Prom'].mean():.2f}")
        m3.metric("Tiendas en Excelencia", f"{df_c['Cumple'].sum()}")

        st.markdown("---")
        
        # Renombramos columnas para el encabezado final
        ranking = df_c[[col_tienda, 'Conv%', 'Ticket_Prom', 'Cumple']].sort_values(
            by=['Cumple', 'Conv%'], ascending=[False, False]
        )
        
        # Limpieza de nombres para la tabla
        tabla_final = ranking.drop(columns=['Cumple'])
        tabla_final.columns = ['Tienda', 'Conversión', 'Ticket Promedio']
        
        # Desplegar tabla con estilo
        st.table(tabla_final.style.format({
            'Conversión': '{:.2f}%',
            'Ticket Promedio': '{:.2f}'
        }))
        
else:
    st.warning("⚠️ Sube el archivo de 'Conversion' a GitHub para visualizar los datos.")

st.markdown("<p style='text-align: center; color: gray;'>Gestión Estratégica Occidente | LAE José Estrada</p>", unsafe_allow_html=True)
