import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Monitor Comercial Occidente", layout="wide")

# --- ESTILO GLOBAL INTERACTIVO ---
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
    
    /* Estilos para las tarjetas de KPI */
    .kpi-box {
        background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 8px;
        padding: 15px; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .kpi-title { font-size: 14px; color: #555; font-weight: bold; text-transform: uppercase; }
    .kpi-value { font-size: 24px; color: #E30613; font-weight: bold; margin: 5px 0; }
    .kpi-delta { font-size: 15px; font-weight: bold; }
    </style>
    <h1 class="main-title">🔴 MONITOR COMERCIAL OCCIDENTE</h1>
    """, unsafe_allow_html=True)

def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith(('.xlsx', '.csv'))]
    return sorted(archivos)[-1] if archivos else None

archivo_conv = buscar_archivo('Conversion')
archivo_modelos = buscar_archivo('Venta_Modelos')
archivo_comp = buscar_archivo('Comparativo por Operacion')

# --- FUNCIÓN DE ALERTA BLINDADA ---
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


# --- DEFINICIÓN DE LAS 6 PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 DESEMPEÑO COMERCIAL", 
    "📈 COMPARATIVO ANUAL",
    "👟 TOP 20 TIENDA", 
    "🌍 TOP 20 ZONA", 
    "🧭 RUTA DEL CLIENTE",
    "🎓 CAPACITACIÓN"
])

# --- PESTAÑA 1: DESEMPEÑO COMERCIAL ---
with tab1:
    if archivo_conv:
        df_c = pd.read_excel(archivo_conv) if archivo_conv.endswith('.xlsx') else pd.read_csv(archivo_conv)
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
                if "✅" in resultado_alerta: st.success(resultado_alerta)
                else: st.error(resultado_alerta)

# --- PESTAÑA 2: COMPARATIVO ANUAL ---
with tab2:
    if archivo_comp:
        st.subheader("📊 Análisis Comparativo Puro de Calzado (2025 vs. 2026)")
        df_op = pd.read_excel(archivo_comp) if archivo_comp.endswith('.xlsx') else pd.read_csv(archivo_comp)
        
        c_ano = next((c for c in df_op.columns if 'año' in c.lower() or 'ano' in c.lower()), df_op.columns[0])
        c_tda = next((c for c in df_op.columns if 'tienda' in c.lower() or 'sucursal' in c.lower()), df_op.columns[2])
        c_prs = next((c for c in df_op.columns if 'pares' in c.lower() or 'cant' in c.lower()), None)
        c_imp = next((c for c in df_op.columns if 'importe' in c.lower() or 'peso' in c.lower() or 'monto' in c.lower()), None)
        c_prov = next((c for c in df_op.columns if 'prov' in c.lower()), None)
        c_tipo = next((c for c in df_op.columns if 'tipo' in c.lower() or 'concepto' in c.lower()), None)
        
        if c_prs and c_imp:
            df_op[c_tda] = df_op[c_tda].astype(str).str.strip()
            df_op = df_op[~df_op[c_tda].str.contains('3004|3015', na=False)]
            if c_prov:
                df_op = df_op[~df_op[c_prov].astype(str).str.strip().isin(['415', '426', '427'])]
            if c_tipo:
                df_op = df_op[~df_op[c_tipo].astype(str).str.contains('BOLSA|REUSABLE|BOLSO', case=False, na=False)]
            
            resumen = df_op.groupby([c_tda, c_ano])[[c_prs, c_imp]].sum().unstack(fill_value=0)
            resumen.columns = ['Pares 2025', 'Pares 2026', 'Pesos 2025', 'Pesos 2026']
            resumen = resumen.reset_index()
            resumen.columns = ['TIENDA', 'PARES 2025', 'PARES 2026', 'PESOS 2025', 'PESOS 2026']
            
            resumen['VAR PARES %'] = ((resumen['PARES 2026'] - resumen['PARES 2025']) / resumen['PARES 2025']) * 100
            resumen['VAR PESOS %'] = ((resumen['PESOS 2026'] - resumen['PESOS 2025']) / resumen['PESOS 2025']) * 100
            
            tot_p25, tot_p26 = resumen['PARES 2025'].sum(), resumen['PARES 2026'].sum()
            tot_w25, tot_w26 = resumen['PESOS 2025'].sum(), resumen['PESOS 2026'].sum()
            var_p_global = ((tot_p26 - tot_p25) / tot_p25) * 100
            var_w_global = ((tot_w26 - tot_w25) / tot_w25) * 100
            
            c1, c2 = st.columns(2)
            with c1:
                signo_p = "+" if var_p_global >= 0 else ""
                col_p = "#155724" if var_p_global >= 0 else "#721c24"
                st.markdown(f"""
                    <div class="kpi-box">
                        <div class="kpi-title">📦 Total Pares Zona Occidente</div>
                        <div class="kpi-value">{tot_p26:,.0f} Pares</div>
                        <div class="kpi-delta" style="color: {col_p};">Variación: {signo_p}{var_p_global:.2f}% vs 2025</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                signo_w = "+" if var_w_global >= 0 else ""
                col_w = "#155724" if var_w_global >= 0 else "#721c24"
                st.markdown(f"""
                    <div class="kpi-box">
                        <div class="kpi-title">💰 Total Ventas ($) Zona Occidente</div>
                        <div class="kpi-value">${tot_w26:,.2f} MXN</div>
                        <div class="kpi-delta" style="color: {col_w};">Variación: {signo_w}{var_w_global:.2f}% vs 2025</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.write("<br>", unsafe_allow_html=True)
            
            tabla_comp = resumen[['TIENDA', 'PARES 2025', 'PARES 2026', 'VAR PARES %', 'PESOS 2025', 'PESOS 2026', 'VAR PESOS %']].sort_values(by='VAR PARES %', ascending=False).reset_index(drop=True)
            
            def color_variacion(val):
                if isinstance(val, (int, float)):
                    color = '#d4edda' if val >= 0 else '#f8d7da'
                    texto = '#155724' if val >= 0 else '#721c24'
                    return f'background-color: {color}; color: {texto}; font-weight: bold;'
                return ''

            st.table(tabla_comp.style.map(color_variacion, subset=['VAR PARES %', 'VAR PESOS %']).format({
                'PARES 2025': '{:,.0f}', 'PARES 2026': '{:,.0f}', 'VAR PARES %': '{:+.2f}%',
                'PESOS 2025': '${:,.2f}', 'PESOS 2026': '${:,.2f}', 'VAR PESOS %': '{:+.2f}%'
            }))

# --- PROCESAMIENTO FILTRADO PARA RANKINGS ---
if archivo_modelos:
    df_m = pd.read_excel(archivo_modelos) if archivo_modelos.endswith('.xlsx') else pd.read_csv(archivo_modelos)
    col_m = next((c for c in df_m.columns if c.lower() in ['clave', 'modelo', 'estilo']), df_m.columns[1])
    col_p = next((c for c in df_m.columns if c.lower() in ['pares', 'cantidad', 'venta']), df_m.columns[2])
    col_t = next((c for c in df_m.columns if c.lower() in ['tienda', 'sucursal']), df_m.columns[0])
    col_prov = next((c for c in df_m.columns if 'prov' in c.lower()), None)

    df_m = df_m[~df_m[col_t].astype(str).str.contains('3004|3015', na=False)]
    if col_prov:
        df_m = df_m[~df_m[col_prov].astype(str).isin(['415', '426', '427'])]
    df_m = df_m[~df_m[col_m].astype(str).str.contains('BOLSA|REUSABLE', case=False, na=False)]

    def resaltar_top_5(data):
        estilo = pd.DataFrame('', index=data.index, columns=data.columns)
        estilo.iloc[0:5, :] = 'background-color: #d1e7dd; color: #0f5132; font-weight: bold'
        return estilo

    with tab3:
        tiendas = sorted(df_m[col_t].unique())
        t_sel = st.selectbox("Selecciona Tienda:", tiendas)
        df_tienda_data = df_m[df_m[col_t] == t_sel].groupby(col_m)[col_p].sum().reset_index()
        top_t = df_tienda_data.sort_values(by=col_p, ascending=False).head(20).reset_index(drop=True)
        top_t.columns = ['MODELO', 'PARES VENDIDOS']
        st.table(top_t.style.apply(resaltar_top_5, axis=None))

    with tab4:
        st.subheader("🌍 Consolidado Zona Occidente")
        df_z = df_m.groupby(col_m)[col_p].sum().reset_index()
        top_z = df_z.sort_values(by=col_p, ascending=False).head(20).reset_index(drop=True)
        top_z.columns = ['MODELO', 'PARES VENDIDOS']
        st.table(top_z.style.apply(resaltar_top_5, axis=None))

# --- PESTAÑA 5: RUTA DEL CLIENTE ---
with tab5:
    st.subheader("🧭 Protocolo Operativo en Piso de Venta")
    nombre_imagen = "RC Zona Occidente.png"
    if os.path.exists(nombre_imagen):
        st.image(nombre_imagen, use_container_width=True)
    else:
        st.warning("⚠️ La imagen 'RC Zona Occidente.png' aún no se encuentra en GitHub.")

# --- PESTAÑA 6: PORTAL DE CAPACITACIÓN Y MANUAL DE INTEGRACIÓN ---
with tab6:
    st.markdown("## 🎓 Centro de Capacitación y Desarrollo Operativo")
    st.write("Bienvenido al espacio interactivo para el fortalecimiento del sentido de pertenencia y alineación comercial de la Zona Occidente.")
    
    # Layout de dos columnas: Izquierda Videos de Capacitación, Derecha el Manual Estratégico Completo
    col_izq, col_der = st.columns([1, 1])
    
    with col_izq:
        # 📹 TITULO CORREGIDO EN LA PARTE AUDIOVISUAL
        st.markdown("### 📹 Videos de Capacitación para el Personal")
        st.video("https://youtu.be/688Bi49rI30")
        st.caption("Material audiovisual interactivo para la alineación del equipo comercial.")
        
    with col_der:
        st.markdown("### 📘 Manual de Integración a Tiendas Flexi")
        
        # 🎯 PUNTO UNO: PROPÓSITO DEL MONITOR
        with st.expander("🎯 1. PROPÓSITO DEL MONITOR COMERCIAL"):
            st.markdown("""
            Este monitor interactivo fue desarrollado bajo la dirección del **LAE. José Martín Estrada Cabrera** con el objetivo de centralizar, automatizar y auditar los indicadores comerciales clave de las **21 tiendas físicas** de la Zona Occidente.
            
            **Metas Estratégicas de la Zona:**
            * 👟 **Ticket Promedio:** Meta de 1.29 unidades (enfocado exclusivamente en calzado puro).
            * 📊 **Conversión Mínima:** Meta de 10.90% en el piso de venta.
            """)
            
        # 📝 PUNTO DOS: INTRODUCCIÓN DEL MANUAL
        with st.expander("📝 2. OBJETIVO DEL MANUAL Y FILOSOFÍA"):
            st.markdown("""
            **Plan de Retención de Personal y Fortalecimiento del Sentido de Pertenencia**
            
            **Objetivo General:**
            Establecer un proceso de acogida estandarizado que reduzca la rotación de personal en los primeros 90 días, transformando la incorporación en una experiencia de bienvenida profundamente profesional y humana.
            
            *La permanencia del personal de nueva contratación no depende únicamente de las condiciones laborales, sino de la calidad de su integración inicial. Este espacio presenta los pilares fundamentales para asegurar que el nuevo colaborador se sienta valorado, guiado y conectado con los objetivos de la organización desde su primer día.*
            """)
            
        with st.expander("🤝 3. PILAR I: BIENVENIDA (LOGÍSTICA Y ORDEN)"):
            st.markdown("""
            **Concepto:** Proyectar orden y profesionalismo. La preparación del entorno de trabajo es el primer mensaje que el colaborador recibe sobre la cultura de la empresa.
            
            **La Acción:** Asegurarse de que el espacio físico esté impecable, las herramientas de trabajo (computadora, accesos, sistemas) estén configuradas y el uniforme de la talla correcta esté listo sobre su lugar antes de que el colaborador cruce la puerta (en la medida de lo posible).
            
            **El Impacto:** Elimina la ansiedad e incertidumbre del primer día. Comunica de forma implícita: *'Te estábamos esperando y tu llegada es importante para nosotros'*.
            """)
            
        with st.expander("👥 4. PILAR II: ACOMPAÑAMIENTO (SISTEMA DE MENTORÍA)"):
            st.markdown("""
            **Concepto:** Eliminar la 'soledad del novato' mediante el sistema de compañero guía.
            
            **La Acción:** Designar a un colaborador con experiencia y actitud positiva para que actúe como mentor durante la primera semana. Este guía resolverá dudas cotidianas, presentará al resto del equipo y explicará las dinámicas no escritas de la tienda.
            
            **El Impacto:** Acelera la curva de aprendizaje social y técnico. Reduce el miedo a cometer errores básicos y crea un vínculo de confianza inmediato en el piso de venta.
            """)
            
        with st.expander("🧭 5. PILAR III: CLARIDAD DEL PROPÓSITO (KPIs)"):
            st.markdown("""
            **Concepto:** Conectar las tareas diarias con el impacto real en el éxito de la zona y la misión de la empresa.
            
            **La Acción:** Realizar una sesión de alineación donde se explique no solo 'qué' debe hacer, sino 'por qué' su rol es vital para alcanzar los objetivos generales. Mostrar cómo su esfuerzo diario contribuye directamente al bienestar del cliente y a la salud del equipo.
            
            **Enfoque Comercial Zona Occidente:**
            Todo colaborador de nuevo ingreso debe comprender que cuidamos con excelencia comercial dos indicadores vitales de calzado puro:
            * 👟 **Ticket Promedio:** Meta de 1.29 unidades por ticket.
            * 📊 **Conversión:** Meta de 10.90% en piso de venta.
            
            **El Impacto:** Genera compromiso emocional. Un colaborador que encuentra propósito en su trabajo desarrolla una lealtad que va más allá de la oferta económica.
            """)
            
        with st.expander("📈 6. PILAR IV: METAS DE CORTO PLAZO"):
            st.markdown("""
            **Concepto:** Brindar claridad absoluta sobre las expectativas de desempeño en la etapa crítica de adaptación.
            
            **La Acción:** Establecer objetivos específicos, medibles y alcanzables para la primera semana, los primeros 15 días y el primer mes. Brindar retroalimentación constructiva al finalizar cada etapa.
            
            **El Impacto:** Reduce la frustración causada por la ambigüedad. Permite que el colaborador celebre victorias tempranas y desarrolle la autoconfianza necesaria para su profesionalización.
            """)
            
        with st.expander("🎉 7. PILAR V: VINCULACIÓN SOCIAL"):
            st.markdown("""
            **Concepto:** Humanizar el entorno laboral y fomentar la integración grupal.
            
            **La Acción:** Organizar activamente momentos de convivencia (como una dinámica de presentación formal) donde el equipo actual reciba y arrope al nuevo integrante de la sucursal.
            
            **El Impacto:** Rompe las barreras invisibles entre el personal antiguo y el nuevo. El sentido de pertenencia a un grupo social es el factor de retención más potente ante ofertas de la competencia.
            
            ---
            *Nota Final: La integración no termina al finalizar el primer día; es un proceso continuo de acompañamiento. El éxito de este manual reside en la consistencia con la que el liderazgo de la tienda aplique cada uno de estos puntos con cada nuevo integrante.*
            """)

# PIE DE PÁGINA
st.markdown("""
    <div class="footer">
        © 2026 Gerencia Comercial Zona Occidente | KPIs Administrados por LAE. José Martín Estrada Cabrera
    </div>
    """, unsafe_allow_html=True)
