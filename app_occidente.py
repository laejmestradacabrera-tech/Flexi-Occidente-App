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
    /* Estilo para los encabezados de la tabla */
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
        
        # Definición de Metas
        meta_conv, meta_tkt = 10.9, 1.29
        
        # --- LÓGICA DEL SEMÁFORO ---
        def aplicar_color(row):
            cumple_conv = row['Conv%'] >= meta_conv
            cumple_tkt = row['Ticket_Prom'] >= meta_tkt
            
            if cumple_conv and cumple_tkt:
                return ['background-color: #d4edda; color: #155724'] * 3  # Verde (Ambos)
            elif cumple_conv or cumple_tkt:
                return ['background-color: #fff3cd; color: #856404'] * 3  # Amarillo (Uno)
            else:
                return ['background-color: #f8d7da; color: #721c24'] * 3  # Rojo (Ninguno)

        # Contadores para las métricas
        excelencia = df_c[(df_c['Conv%'] >= meta_conv) & (df_c['Ticket_Prom'] >= meta_tkt)].shape[0]
        alerta = df_c[(df_c['Conv%'] < meta_conv) & (df_c['Ticket_Prom'] < meta_tkt)].shape[0]

        # Métricas principales
        m1, m2, m3 = st.columns(3)
        m1.metric("Promedio Zona Conv.", f"{df_c['Conv%'].mean():.2f}%")
        m2.metric("Promedio Zona Tkt.", f"{df_c['Ticket_Prom'].mean():.2f}")
        m3.metric("Tiendas en Excelencia", f"{excelencia}")

        st.markdown("---")
        
        # Ordenar: Excelencia primero, luego amarillos, luego rojos
        df_c['Prioridad'] = df_c.apply(lambda r: 2 if (r['Conv%'] >= meta_conv and r['Ticket_Prom'] >= meta_tkt) 
                                     else (1 if (r['Conv%'] >= meta_conv or r['Ticket_Prom'] >= meta_tkt) else 0), axis=1)
        
        ranking = df_c.sort_values(by=['Prioridad', 'Conv%'], ascending=[False, False])
        
        # Seleccionamos y renombramos columnas para la tabla final
        tabla_final = ranking[[col_tienda, 'Conv%', 'Ticket_Prom']]
        tabla_final.columns = ['Tienda', 'Conversión', 'Ticket Promedio']
        
        # Desplegar tabla con el semáforo aplicado
        st.table(tabla_final.style.apply(aplicar_color, axis=1).format({
            'Conversión': '{:.2f}%',
            'Ticket Promedio': '{:.2f}'
        }))
        
        # Leyenda del monitor
        st.caption("🟢 Verde: Cumple ambos | 🟡 Amarillo: Cumple uno | 🔴 Rojo: No cumple ninguno")
        
else:
    st.warning("⚠️ Sube el archivo de 'Conversion' a GitHub para visualizar los datos.")

st.markdown("<p style='text-align: center; color: gray;'>Gestión Estratégica Occidente | LAE José Estrada</p>", unsafe_allow_html=True)
