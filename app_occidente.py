import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- ESTILO GLOBAL ---
st.markdown("""
    <style>
    .main-title {
        text-align: center; color: #E30613; font-size: 32px; font-weight: bold;
        border-bottom: 3px solid #E30613; padding-bottom: 10px; margin-bottom: 20px;
    }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: white; color: #666; text-align: center;
        padding: 8px; font-size: 13px; border-top: 1px solid #ddd;
        z-index: 999; font-weight: bold;
    }
    th {
        background-color: #E30613 !important; color: white !important;
        font-weight: bold !important; text-transform: uppercase !important;
        text-align: center !important; padding: 12px !important;
    }
    td { text-align: center !important; font-size: 15px !important; }
    </style>
    <h1 class="main-title">🔴 MONITOR COMERCIAL OCCIDENTE</h1>
    """, unsafe_allow_html=True)

def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith('.xlsx')]
    return sorted(archivos)[-1] if archivos else None

archivo_conv = buscar_archivo('Conversion')
# buscar archivo venta modelos
archivo_modelos = buscar_archivo('Venta_Modelos')


# --- FUNCIÓN DE ALERTA BLINDADA (SÓLO CON ARCHIVO MODIFICADO) ---
@st.cache_data(show_spinner=False)
def enviar_correo_por_modificacion(df_ranking, ruta_archivo, ultima_modificacion, tienda_objetivo="56"):
    fila_tienda = df_ranking[df_ranking['TIENDA'].astype(str).str.contains(tienda_objetivo, na=False)]
    
    if not fila_tienda.empty:
        conversion_actual = float(fila_tienda.iloc[0]['CONVERSIÓN'])
        ticket_actual = float(fila_tienda.iloc[0]['TICKET PROMEDIO'])
        
        meta_conv = 10.9
        meta_ticket = 1.29
        
        logro_conv = conversion_actual >= meta_conv
        logro_ticket = ticket_actual >= meta_ticket
        
        desviacion_conv = conversion_actual - meta_conv
        desviacion_ticket = ticket_actual - meta_ticket
        
        try:
            remitente = st.secrets["CORREO_REMITENTE"]
            password = st.secrets["CORREO_PASSWORD"]
            destinatario = "fleoutgdl@divec-flexi.com"
            
            asunto = f"📊 Reporte de Desviaciones Meta - Tienda {tienda_objetivo}"
            
            cuerpo = f"Estimada Ana Leticia y equipo de Plazas Outlet (Tienda {tienda_objetivo}):\n\n"
            cuerpo += "Les compartimos el análisis de desviaciones frente a las metas establecidas:\n\n"
            
            if logro_conv:
                cuerpo += f"✅ CONVERSIÓN: {conversion_actual:.2f}% (Supera la meta por +{desviacion_conv:.2f}%)\n"
            else:
                cuerpo += f"❌ CONVERSIÓN: {conversion_actual:.2f}% (Faltan {abs(desviacion_conv):.2f}% para la meta de {meta_conv}%)\n"
                
            if logro_ticket:
                cuerpo += f"✅ TICKET PROMEDIO: {ticket_actual:.2f} pares (Supera la meta por +{desviacion_ticket:.2f} pares)\n\n"
            else:
                cuerpo += f"❌ TICKET PROMEDIO: {ticket_actual:.2f} pares (Faltan {abs(desviacion_ticket):.2f} pares para la meta de {meta_ticket} de calzado)\n\n"
                
            if logro_conv and logro_ticket:
                cuerpo += "🏆 ¡Muchas felicidades por lograr ambos indicadores! Excelente desempeño en el piso de venta, sigan manteniendo ese ritmo."
            elif logro_conv or logro_ticket:
                cuerpo += "⚠️ ALERTA: Se está logrando solo un indicador. Es necesario ajustar la estrategia en el indicador faltante para asegurar el resultado completo."
            else:
                cuerpo += "📉 ATENCIÓN: No se logró ninguno de los indicadores establecidos. Hay que trabajar con urgencia y enfocar todo el esfuerzo para alcanzar las metas."

            msg = MIMEText(cuerpo)
            msg['Subject'] = asunto
            msg['From'] = remitente
            msg['To'] = destinatario
            
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(remitente, password)
            server.sendmail(remitente, [destinatario], msg.as_string())
            server.quit()
            return f"✅ Alerta de desviación enviada exitosamente a la Tienda {tienda_objetivo} (Plazas Outlet)"
        except Exception as e:
            return f"❌ Error al enviar el correo: {e}"
    return None


# --- AGREGAMOS LA CUARTA PESTAÑA AL MONITOR ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 DESEMPEÑO COMERCIAL", "👟 TOP 20 TIENDA", "🌍 TOP 20 ZONA", "🧭 RUTA DEL CLIENTE"])

# --- PESTAÑA 1: DESEMPEÑO COMERCIAL ---
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
            
            ranking = df_c[[col_tienda, 'CONVERSIÓN', 'TICKET PROMEDIO']].sort_values(by='CONVERSIÓN', ascending=False).reset_index(drop=True)
            ranking.insert(0, 'POS', range(1, len(ranking) + 1))
            ranking.columns = ['#', 'TIENDA', 'CONVERSIÓN', 'TICKET PROMEDIO']

            def color_semaforo(row):
                c_conv = row['CONVERSIÓN'] >= meta_conv
                c_tkt = row['TICKET PROMEDIO'] >= meta_tkt
                if c_conv and c_tkt: return ['background-color: #d4edda; color: #155724'] * 4
                elif c_conv or c_tkt: return ['background-color: #fff3cd; color: #856404'] * 4
                else: return ['background-color: #f8d7da; color: #721c24'] * 4

            st.table(ranking.style.apply(color_semaforo, axis=1).format({'CONVERSIÓN': '{:.2f}%', 'TICKET PROMEDIO': '{:.2f}'}))
            
            mod_time = os.path.getmtime(archivo_conv)
            resultado_alerta = enviar_correo_por_modificacion(ranking, archivo_conv, mod_time, tienda_objetivo="56")
            
            if resultado_alerta:
                if "✅" in resultado_alerta:
                    st.success(resultado_alerta)
                else:
                    st.error(resultado_alerta)

# --- PROCESAMIENTO FILTRADO PARA RANKINGS (SOLO ZAPATO) ---
if archivo_modelos:
    df_m = pd.read_excel(archivo_modelos)
    col_m = next((c for c in df_m.columns if c.lower() in ['clave', 'modelo', 'estilo']), df_m.columns[1])
    col_p = next((c for c in df_m.columns if c.lower() in ['pares', 'cantidad', 'venta']), df_m.columns[2])
    col_t = next((c for c in df_m.columns if c.lower() in ['tienda', 'sucursal']), df_m.columns[0])
    col_prov = next((c for c in df_m.columns if 'prov' in c.lower() or 'provee' in c.lower()), None)

    df_m = df_m[~df_m[col_t].astype(str).str.contains('3004|3015', na=False)]

    if col_prov:
        df_m = df_m[~df_m[col_prov].astype(str).isin(['415', '426', '427'])]
    df_m = df_m[~df_m[col_m].astype(str).str.contains('BOLSA|REUSABLE', case=False, na=False)]

    def resaltar_top_5(data):
        estilo = pd.DataFrame('', index=data.index, columns=data.columns)
        estilo.iloc[0:5, :] = 'background-color: #d1e7dd; color: #0f5132; font-weight: bold'
        return estilo

    with tab2:
        tiendas = sorted(df_m[col_t].unique())
        t_sel = st.selectbox("Selecciona Tienda:", tiendas)
        df_tienda_data = df_m[df_m[col_t] == t_sel].groupby(col_m)[col_p].sum().reset_index()
        top_t = df_tienda_data.sort_values(by=col_p, ascending=False).head(20).reset_index(drop=True)
        top_t.columns = ['MODELO', 'PARES VENDIDOS']
        st.table(top_t.style.apply(resaltar_top_5, axis=None))

    with tab3:
        st.subheader("🌍 Consolidado Zona Occidente")
        df_z = df_m.groupby(col_m)[col_p].sum().reset_index()
        top_z = df_z.sort_values(by=col_p, ascending=False).head(20).reset_index(drop=True)
        top_z.columns = ['MODELO', 'PARES VENDIDOS']
        st.table(top_z.style.apply(resaltar_top_5, axis=None))

# --- PESTAÑA 4: MOSTRAR LA INFOGRAFÍA EN ALTA DEFINICIÓN ---
with tab4:
    st.subheader("🧭 Protocolo de Venta Flexi - Zona Occidente")
    nombre_imagen = "RC Zona Occidente.png"
    
    if os.path.exists(nombre_imagen):
        # Muestra la imagen centrada y aprovecha el ancho completo de la pantalla
        st.image(nombre_imagen, use_container_width=True)
    else:
        st.warning("⚠️ La imagen 'RC Zona Occidente.png' aún no se encuentra en la carpeta de GitHub. Por favor, súbela para habilitar la visualización.")

# PIE DE PÁGINA
st.markdown("""
    <div class="footer">
        KPIs zona Occidente/LAE. José Martín Estrada
    </div>
    """, unsafe_allow_html=True)
