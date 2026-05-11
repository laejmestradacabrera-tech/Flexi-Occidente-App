import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- ESTILO PERSONALIZADO (ROJO FLEXI Y TABLA LIMPIA) ---
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #E30613;
        font-size: 45px;
        font-weight: bold;
        border-bottom: 3px solid #E30613;
        padding-bottom: 10px;
        margin-bottom: 25px;
    }
    /* Eliminar la numeración de la izquierda en las tablas */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
    <h1 class="main-title">🔴 MONITOR COMERCIAL OCCIDENTE</h1>
    """, unsafe_allow_html=True)

def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith('.xlsx')]
    return sorted(archivos)[-1] if archivos else None

# --- LÓGICA DE CARGA DE DATOS ---
archivo_conv = buscar_archivo('Conversion')

tab1, tab2 = st.tabs(["📊 DESEMPEÑO DE TIENDAS", "💰 RANKING DE VENTAS"])

with tab1:
    if archivo_conv:
        df_c = pd.read_excel(archivo_conv)
        # Limpieza de administrativos
        df_c = df_c[~df_c.iloc[:,0].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)]
        
        # Identificar columnas
        col_tienda = next((c for c in df_c.columns if 'Tienda' in c or 'TIENDA' in c), df_c.columns[0])
        col_conv_real = next((c for c in df_c.columns if 'Conv' in c and 'Actual' in c), None)
        col_tkt_real = next((c for c in df_c.columns if 'Ticket' in c or 'Uds/Tkt' in c or 'Prom' in c), None)
        
        if col_conv_real and col_tkt_real:
            df_c['Conv%'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
            df_c['Ticket_Prom'] = df_c[col_tkt_real]
            
            # Definición de Metas
            meta_conv = 10.9
            meta_tkt = 1.29
            
            # Marcamos quiénes cumplen ambos para poder ordenarlos arriba
            df_c['Excelencia'] = (df_c['Conv%'] >= meta_conv) & (df_c['Ticket_Prom'] >= meta_tkt)
            
            # Métricas superiores
            m1, m2, m3 = st.columns(3)
            m1.metric("Promedio Zona Conv.", f"{df_c['Conv%'].mean():.2f}%")
            m2.metric("Promedio Zona Tkt.", f"{df_c['Ticket_Prom'].mean():.2f}")
            m3.metric("Tiendas en Excelencia", f"{df_c['Excelencia'].sum()}")

            st.markdown("---")
            st.subheader(f"🏆 RANKING OPERATIVO (Ordenado por cumplimiento)")
            
            # Ordenamos: primero las de excelencia, y dentro de eso, por mayor conversión
            ranking = df_c[[col_tienda, 'Conv%', 'Ticket_Prom', 'Excelencia']].sort_values(
                by=['Excelencia', 'Conv%'], 
                ascending=[False, False]
            )
            
            # Función para resaltar las filas que cumplen la meta (Opcional visual)
            def resaltar_excelencia(s):
                return ['background-color: #d4edda' if s.Excelencia else '' for _ in s]

            # Mostramos la tabla filtrando la columna auxiliar 'Excelencia' para que no se vea
            tabla_final = ranking.drop(columns=['Excelencia'])
            
            st.table(tabla_final.style.format({
                'Conv%': '{:.2f}%',
                'Ticket_Prom': '{:.2f}'
            }))
            
            st.caption(f"Nota: Las tiendas al principio de la lista cumplen con la Doble Meta (Conv ≥ {meta_conv}% y Tkt ≥ {meta_tkt})")
            
        else:
            st.error("❌ No se detectaron las columnas de datos correctamente.")
    else:
        st.warning("⚠️ Esperando archivo de 'Conversión'...")

with tab2:
    st.info("ℹ️ Sube el reporte de 'Ventas' a GitHub para activar el ranking de ingresos.")

st.markdown("<br><p style='text-align: center; color: gray;'>Gestión Estratégica Occidente | LAE José Estrada</p>", unsafe_allow_html=True)
