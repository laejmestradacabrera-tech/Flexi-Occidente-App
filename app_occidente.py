import streamlit as st
import pandas as pd
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- 2. ESTILO LIMPIO Y PROFESIONAL ---
st.markdown("""
    <style>
    .main-title {
        text-align: center; color: #E30613; font-size: 32px; font-weight: bold;
        border-bottom: 3px solid #E30613; padding-bottom: 10px; margin-bottom: 20px;
    }
    /* ENCABEZADOS TABLA DESEMPEÑO */
    th {
        background-color: #E30613 !important;
        color: white !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        text-align: center !important;
        padding: 12px !important;
    }
    td { 
        text-align: center !important; 
        font-size: 15px !important; 
        padding: 10px !important;
    }
    /* ELIMINAR COLUMNA DE ÍNDICE */
    thead tr th:first-child { display: none !important; }
    tbody th { display: none !important; }
    </style>
    <h1 class="main-title">🔴 MONITOR COMERCIAL OCCIDENTE</h1>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA DE DATOS ---
def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith('.xlsx')]
    return sorted(archivos)[-1] if archivos else None

archivo_conv = buscar_archivo('Conversion')

# --- 4. MÓDULO ÚNICO: DESEMPEÑO COMERCIAL ---
if archivo_conv:
    st.subheader("📊 DESEMPEÑO COMERCIAL (CONVERSIÓN Y TICKET)")
    
    df_c = pd.read_excel(archivo_conv)
    # Limpieza de filas no deseadas
    df_c = df_c[~df_c.iloc[:,0].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)]
    
    col_tienda = next((c for c in df_c.columns if 'Tienda' in c or 'TIENDA' in c), df_c.columns[0])
    col_conv_real = next((c for c in df_c.columns if 'Conv' in c and 'Actual' in c), None)
    col_tkt_real = next((c for c in df_c.columns if 'Ticket' in c or 'Uds/Tkt' in c or 'Prom' in c), None)
    
    if col_conv_real and col_tkt_real:
        # Metas establecidas
        meta_conv, meta_tkt = 10.9, 1.29
        
        # Cálculos
        df_c['CONVERSIÓN'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
        df_c['TICKET PROMEDIO'] = df_c[col_tkt_real]
        df_c['FALTANTE CONV.'] = df_c['CONVERSIÓN'].apply(lambda x: "✅" if x >= meta_conv else f"{x - meta_conv:.2f}%")
        df_c['FALTANTE TKT.'] = df_c['TICKET PROMEDIO'].apply(lambda x: "✅" if x >= meta_tkt else f"{x - meta_tkt:.2f}")

        # Lógica de colores por fila completa
        def color_desempeno(row):
            c_conv = row['CONVERSIÓN'] >= meta_conv
            c_tkt = row['TICKET PROMEDIO'] >= meta_tkt
            if c_conv and c_tkt:
                return ['background-color: #d4edda; color: #155724'] * 5 # Verde
            elif c_conv or c_tkt:
                return ['background-color: #fff3cd; color: #856404'] * 5 # Amarillo
            else:
                return ['background-color: #f8d7da; color: #721c24'] * 5 # Rojo

        # Ordenar por Conversión
        ranking = df_c[[col_tienda, 'CONVERSIÓN', 'FALTANTE CONV.', 'TICKET PROMEDIO', 'FALTANTE TKT.']].sort_values(by='CONVERSIÓN', ascending=False)
        ranking.columns = ['TIENDA', 'CONVERSIÓN', 'FALTANTE CONV.', 'TICKET PROMEDIO', 'FALTANTE TKT.']
        
        # Mostrar tabla única
        st.table(ranking.style.apply(color_desempeno, axis=1).format({'CONVERSIÓN': '{:.2f}%', 'TICKET PROMEDIO': '{:.2f}'}))
else:
    st.warning("⚠️ No se encontró el archivo de 'Conversion' en el repositorio.")

st.markdown("<p style='text-align: center; color: gray; font-size: 10px;'>Gestión Occidente | LAE José Estrada</p>", unsafe_allow_html=True)
