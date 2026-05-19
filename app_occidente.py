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

# --- DEFINICIÓN DE LAS 7 PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 DESEMPEÑO COMERCIAL", 
    "📈 COMPARATIVO MENSUAL",
    "👟 TOP 20 TIENDA", 
    "🌍 TOP 20 ZONA", 
    "🧭 RUTA DEL CLIENTE",
    "🎓 CAPACITACIÓN",
    "🔄 NIVELACIÓN DE STOCK"
])

# --- PESTAÑAS DEL MONITOR MANTEINDAS AL 100% ---
with tab1:
    if archivo_conv:
        df_c = pd.read_excel(archivo_conv) if archivo_conv.endswith('.xlsx') else pd.read_csv(archivo_conv)
        df_c = df_c[~df_c.iloc[:,0].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)]
        col_tienda = next((c for c in df_c.columns if 'Tienda' in c or 'TIENDA' in c), df_c.columns[0])
        col_conv_real = next((c for c in df_c.columns if 'Conv' in c and 'Actual' in c), None)
        col_tkt_real = next((c for c in df_c.columns if 'Ticket' in c or 'Uds/Tkt' in c or 'Prom' in c), None)
        if col_conv_real and col_tkt_real:
            df_c['CONVERSIÓN'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
            df_c['TICKET PROMEDIO'] = df_c[col_tkt_real]
            ranking = df_c[[col_tienda, 'CONVERSIÓN', 'TICKET PROMEDIO']].sort_values(by='CONVERSIÓN', ascending=False).reset_index(drop=True)
            ranking.insert(0, 'POS', range(1, len(ranking) + 1))
            ranking.columns = ['#', 'TIENDA', 'CONVERSIÓN', 'TICKET PROMEDIO']
            def color_semaforo(row):
                if row['CONVERSIÓN'] >= 10.9 and row['TICKET PROMEDIO'] >= 1.29: return ['background-color: #d4edda; color: #155724'] * 4
                elif row['CONVERSIÓN'] >= 10.9 or row['TICKET PROMEDIO'] >= 1.29: return ['background-color: #fff3cd; color: #856404'] * 4
                else: return ['background-color: #f8d7da; color: #721c24'] * 4
            st.table(ranking.style.apply(color_semaforo, axis=1).format({'CONVERSIÓN': '{:.2f}%', 'TICKET PROMEDIO': '{:.2f}'}))
            mod_time = os.path.getmtime(archivo_conv)
            resultado_alerta = enviar_correo_por_modificacion(ranking, archivo_conv, mod_time, tienda_objetivo="56")
            if resultado_alerta: st.success(resultado_alerta) if "✅" in resultado_alerta else st.error(resultado_alerta)

with tab2:
    if archivo_comp:
        st.subheader("📊 Análisis Comparativo de Calzado Mensual")
        df_op = pd.read_excel(archivo_comp) if archivo_comp.endswith('.xlsx') else pd.read_csv(archivo_comp)
        c_ano = next((c for c in df_op.columns if 'año' in c.lower() or 'ano' in c.lower()), df_op.columns[0])
        c_tda = next((c for c in df_op.columns if 'tienda' in c.lower() or 'sucursal' in c.lower()), df_op.columns[2])
        c_prs = next((c for c in df_op.columns if 'pares' in c.lower() or 'cant' in c.lower()), None)
        c_imp = next((c for c in df_op.columns if 'importe' in c.lower() or 'peso' in c.lower() or 'monto' in c.lower()), None)
        if c_prs and c_imp:
            df_op[c_tda] = df_op[c_tda].astype(str).str.strip()
            df_op = df_op[~df_op[c_tda].str.contains('3004|3015', na=False)]
            resumen = df_op.groupby([c_tda, c_ano])[[c_prs, c_imp]].sum().unstack(fill_value=0)
            resumen.columns = ['Pares 2025', 'Pares 2026', 'Pesos 2025', 'Pesos 2026']
            resumen = resumen.reset_index()
            resumen.columns = ['TIENDA', 'PARES 2025', 'PARES 2026', 'PESOS 2025', 'PESOS 2026']
            resumen['VAR PARES %'] = ((resumen['PARES 2026'] - resumen['PARES 2025']) / resumen['PARES 2025']) * 100
            resumen['VAR PESOS %'] = ((resumen['PESOS 2026'] - resumen['PESOS 2025']) / resumen['PESOS 2025']) * 100
            st.table(resumen.sort_values(by='VAR PARES %', ascending=False).reset_index(drop=True).style.format({
                'PARES 2025': '{:,.0f}', 'PARES 2026': '{:,.0f}', 'VAR PARES %': '{:+.2f}%',
                'PESOS 2025': '${:,.2f}', 'PESOS 2026': '${:,.2f}', 'VAR PESOS %': '{:+.2f}%'
            }))

if archivo_modelos:
    df_m = pd.read_excel(archivo_modelos) if archivo_modelos.endswith('.xlsx') else pd.read_csv(archivo_modelos)
    col_m = next((c for c in df_m.columns if c.lower() in ['clave', 'modelo', 'estilo']), df_m.columns[1])
    col_p = next((c for c in df_m.columns if c.lower() in ['pares', 'cantidad', 'venta']), df_m.columns[2])
    col_t = next((c for c in df_m.columns if c.lower() in ['tienda', 'sucursal']), df_m.columns[0])
    df_m = df_m[~df_m[col_t].astype(str).str.contains('3004|3015', na=False)]
    with tab3:
        t_sel = st.selectbox("Selecciona Tienda:", sorted(df_m[col_t].unique()))
        st.table(df_m[df_m[col_t] == t_sel].groupby(col_m)[col_p].sum().reset_index().sort_values(by=col_p, ascending=False).head(20).reset_index(drop=True))
    with tab4:
        st.subheader("🌍 Consolidado Zona Occidente")
        st.table(df_m.groupby(col_m)[col_p].sum().reset_index().sort_values(by=col_p, ascending=False).head(20).reset_index(drop=True))

with tab5:
    st.subheader("🧭 Protocolo Operativo en Piso de Venta")
    if os.path.exists("RC Zona Occidente.png"): st.image("RC Zona Occidente.png", use_container_width=True)

# --- PESTAÑA 6: PORTAL DE CAPACITACIÓN RESPALDADO AL 100% ---
with tab6:
    st.markdown("## 🎓 Centro de Capacitación y Desarrollo Operativo")
    c_izq, c_der = st.columns([1, 1])
    with c_izq:
        opciones_video = {"Mi Nómina Flexi": "https://youtu.be/688Bi49rI30", "Tutorial Vales de Zapatos": "https://youtu.be/6hB95lYcL1g", "Tutorial mi Flexi": "https://youtu.be/WVi8geGSeOg"}
        v_sel = st.selectbox("Selecciona material a reproducir:", list(opciones_video.keys()))
        st.video(opciones_video[v_sel])
    with c_der:
        st.markdown("### 📘 Manual de Integración a Tiendas Flexi")
        with st.expander("🎯 1. PROPÓSITO DEL MONITOR COMERCIAL"):
            st.markdown("Monitor interactivo bajo la dirección del **LAE. José Martín Estrada Cabrera**.\n* 👟 **Ticket Promedio:** Meta 1.29 unidades.\n* 📊 **Conversión Mínima:** Meta 10.90%.")
        with st.expander("📝 2. OBJETIVO DEL MANUAL Y FILOSOFÍA"):
            st.markdown("**Plan de Retención de Personal**\n\n*Objetivo:* Reducir la rotación en los primeros 90 días con un proceso de acogida profesional y humano. La permanencia depende de la calidad de la integración inicial.")
        with st.expander("🤝 3. PILAR I: BIENVENIDA (LOGÍSTICA Y ORDEN)"):
            st.markdown("**Concepto:** Proyectar orden. Enviar uniforme de talla correcta y estación impecable antes de su llegada.\n**Impacto:** Elimina la ansiedad del primer día.")
        with st.expander("👥 4. PILAR II: ACOMPAÑAMIENTO (MENTORÍA)"):
            st.markdown("**Concepto:** Sistema de compañero guía contra la soledad del novato.\n**Acción:** Mentor asignado la primera semana para resolver dudas cotidianas.")
        with st.expander("🧭 5. PILAR III: CLARIDAD DEL PROPÓSITO"):
            st.markdown("**Concepto:** Conectar tareas diarias con la misión general de la zona. Explicar las metas de calzado puro (Ticket Promedio 1.29 y Conversión 10.90%) para generar lealtad emocional.")
        with st.expander("📈 6. PILAR IV: METAS DE CORTO PLAZO"):
            st.markdown("**Concepto:** Expectativas claras en periodos críticos.\n**Acción:** Objetivos específicos para la primera semana, 15 días y primer mes con retroalimentación constructiva.\n**Impacto:** El colaborador celebra victorias tempranas.")
        with st.expander("🎉 7. PILAR V: VINCULACIÓN SOCIAL"):
            st.markdown("**Concepto:** Humanizar la integración grupal.\n**Acción:** Dinámicas de presentación formal con el equipo completo.\n**Impacto:** Sentido de pertenencia potente ante ofertas de la competencia.")

# ==============================================================================
# --- PESTAÑA 7: ALGORITMO MAESTRO DE NIVELACIÓN DE ACUERDO A TU CRITERIO ---
# ==============================================================================
with tab7:
    st.subheader("🔄 Algoritmo Maestro de Nivelación de Inventarios (2 Meses)")
    st.write("Análisis directo basado en la base de datos de GitHub: Encontrar surtido óptimo para la tienda en cero sin dejar a nadie en ceros.")

    USUARIO_GE = "laejmestradacabrera-tech"
    REPOSITORIO_GE = "Flexi-Occidente-App"
    NOMBRE_ARCHIVO_GE = "ventas_maestro.csv" 
    URL_GITHUB_MAESTRO = f"https://raw.githubusercontent.com/{USUARIO_GE}/{REPOSITORIO_GE}/main/{NOMBRE_ARCHIVO_GE}"
    
    try:
        df_niv = pd.read_csv(URL_GITHUB_MAESTRO)
        df_niv.fillna(0, inplace=True)
        df_niv['Tienda'] = df_niv['Tienda'].astype(int)
        df_niv = df_niv[~df_niv['Tienda'].isin([3004, 3015])]
        
        tiendas_imanes = [19, 56, 59, 133]

        # Mapeo exacto de columnas de tu ERP según la auditoría de tallas
        def obtener_talla_real(modelo, num_columna):
            mod_str = str(modelo).upper()
            if any(mod_str.startswith(pre) for pre in ['CD', 'CK', 'CY', 'MD', 'VD']):
                tallas_dama = {3:'22', 4:'22.5', 5:'23', 6:'23.5', 7:'24', 8:'24.5', 9:'25', 10:'25.5', 11:'26', 12:'26.5', 13:'27'}
                return tallas_dama.get(num_columna, None)
            elif any(mod_str.startswith(pre) for pre in ['CH', 'MH', 'VH']):
                tallas_hombre = {1:'25', 2:'25.5', 3:'26', 4:'26.5', 5:'27', 6:'27.5', 7:'28', 8:'28.5', 9:'29', 10:'29.5', 11:'30', 12:'30.5', 13:'31'}
                return tallas_hombre.get(num_columna, None)
            elif mod_str.startswith('NM'):
                tallas_nm = {1:'17', 2:'17.5', 3:'18', 4:'18.5', 5:'19', 6:'19.5', 7:'20', 8:'20.5', 9:'21', 10:'21.5'}
                return tallas_nm.get(num_columna, None)
            elif mod_str.startswith('CJ'):
                tallas_cj = {1:'21.5', 2:'22', 3:'22.5', 4:'23', 5:'23.5', 6:'24', 7:'24.5', 8:'25', 9:'25.5', 10:'26', 11:'26.5', 12:'27'}
                return tallas_cj.get(num_columna, None)
            return None

        # Desglose vertical estricto basado en la base de datos de GitHub
        registros_desglosados = []
        for idx, fila in df_niv.iterrows():
            modelo = fila['Modelo']
            tienda = int(fila['Tienda'])
            estatus = str(fila['Estatus']).upper()
            
            for i in range(1, 16):
                talla_nom = obtener_talla_real(modelo, i)
                if talla_nom is not None:
                    existencia_fisica = float(fila.get(f'ex{i}', 0))
                    ventas_acumuladas = float(fila.get(f'v{i}', 0))
                    
                    if existencia_fisica > 0 or ventas_acumuladas > 0:
                        registros_desglosados.append({
                            'Tienda': tienda, 'Modelo': modelo, 'Estatus': estatus, 'Talla': talla_nom,
                            'Stock_Fisico': existencia_fisica, 'Ventas': ventas_acumuladas
                        })
        
        if registros_desglosados:
            df_vertical = pd.DataFrame(registros_desglosados)
            df_agrupado = df_vertical.groupby(['Tienda', 'Modelo', 'Estatus', 'Talla']).agg({
                'Stock_Fisico': 'sum', 'Ventas': 'sum'
            }).reset_index()

            # INTERFAZ DIRECTA: La encargada o tú seleccionan la tienda que tiene el quiebre (La tienda de ABAJO)
            tienda_solicitante = st.selectbox(
                "Selecciona la sucursal que deseas abastacer o auditar sus quiebres (Destino):", 
                sorted(df_agrupado['Tienda'].unique())
            )
            
            propuestas_traspaso = []
            
            # Filtramos los quiebres de la tienda seleccionada (Tiene 0 existencias físicas pero vende)
            df_destino_tda = df_agrupado[(df_agrupado['Tienda'] == tienda_solicitante) & (df_agrupado['Stock_Fisico'] == 0) & (df_agrupado['Ventas'] >= 1)]
            
            for _, fila_destino in df_destino_tda.iterrows():
                modelo = fila_destino['Modelo']
                talla = fila_destino['Talla']
                estatus_mod = fila_destino['Estatus']
                vta_dest = int(fila_destino['Ventas'])
                
                # Buscamos en el resto de las tiendas de la zona quién puede surtir este hueco de forma segura
                grupo_origenes_potenciales = df_agrupado[(df_agrupado['Modelo'] == modelo) & (df_agrupado['Talla'] == talla) & (df_agrupado['Tienda'] != tienda_solicitante)]
                
                for _, fila_origen in grupo_origenes_potenciales.iterrows():
                    t_orig = int(fila_origen['Tienda'])
                    stk_real_orig = int(fila_origen['Stock_Fisico'])
                    
                    # 🔥 CANDADO PILAR 5 DEL ORIGEN: 
                    # Solo se le puede quitar calzado si tiene 2 o más en inventario. Ninguna tienda se queda en 0.
                    # Excepción en Saldos/Promoción: se permite sacar si tiene >= 1 par.
                    if estatus_mod not in ['S', 'P'] and stk_real_orig < 2:
                        continue
                    if estatus_mod in ['S', 'P'] and stk_real_orig < 1:
                        continue
                        
                    if vta_dest > 0 and stk_real_orig > 0:
                        if estatus_mod not in ['S', 'P']:
                            cant_mover = min(stk_real_orig - 1, vta_dest) # Se queda con mínimo 1 par físico en stock
                        else:
                            cant_mover = min(stk_real_orig, vta_dest) # Saldos vacían bodega completo
                            
                        if cant_mover > 0:
                            propuestas_traspaso.append({
                                'Tienda que Envia (Origen)': t_orig,
                                'Modelo': modelo,
                                'Estatus': estatus_mod,
                                'Talla': talla,
                                'Pares a Traspasar': cant_mover,
                                'Prioridad': '🚨 CRÍTICA (Quiebre)' if estatus_mod == 'N' else '📦 EVACUACIÓN (Saldo)'
                            })
                            vta_dest -= cant_mover
            
            # --- CASO COMPLEMENTARIO: MODELOS COMPLETAMENTE NUEVOS SIN MOVIMIENTO EN LA ZONA ---
            df_destino_sin_mov = df_agrupado[(df_agrupado['Tienda'] == tienda_solicitante) & (df_agrupado['Stock_Fisico'] == 0)]
            if tienda_solicitante in tiendas_imanes:
                for _, fila_destino in df_destino_sin_mov.iterrows():
                    modelo = fila_destino['Modelo']
                    talla = fila_destino['Talla']
                    estatus_mod = fila_destino['Estatus']
                    
                    grupo_resto = df_agrupado[(df_agrupado['Modelo'] == modelo) & (df_agrupado['Talla'] == talla) & (df_agrupado['Tienda'] != tienda_solicitante)]
                    total_ventas_zona = grupo_resto['Ventas'].sum()
                    
                    if total_ventas_zona == 0: # Nadie lo ha vendido
                        for _, fila_origen in grupo_resto.iterrows():
                            t_orig = int(fila_origen['Tienda'])
                            stk_real_orig = int(fila_origen['Stock_Fisico'])
                            
                            if estatus_mod not in ['S', 'P'] and stk_real_orig < 2:
                                continue
                            if estatus_mod in ['S', 'P'] and stk_real_orig < 1:
                                continue
                                
                            if stk_real_orig > 0:
                                propuestas_traspaso.append({
                                    'Tienda que Envia (Origen)': t_orig, 'Modelo': modelo, 'Estatus': estatus_mod,
                                    'Talla': talla, 'Pares a Traspasar': 1, 'Prioridad': '🔄 REACTIVACIÓN (Sin Venta)'
                                })
                                break

            df_propuestas = pd.DataFrame(propuestas_traspaso)
            st.success(f"📦 ¡Enlace Perfecto! Base de datos de GitHub analizada bajo tus 5 pilares operativos.")
            
            if not df_propuestas.empty:
                st.write(f"### 📋 Propuestas de Surtido Autorizadas para la Tienda {tienda_solicitante}")
                st.write(f"Para cubrir los quiebres de la Tienda {tienda_solicitante}, solicita retirar calzado de las siguientes sucursales con excedentes:")
                st.dataframe(df_propuestas[['Tienda que Envia (Origen)', 'Modelo', 'Estatus', 'Talla', 'Pares a Traspasar', 'Prioridad']], use_container_width=True)
            else:
                st.info(f"✨ Con base en tus archivos de GitHub, la Tienda {tienda_solicitante} se encuentra perfectamente nivelada (No hay tiendas en la zona con stock $\ge$ 2 en tus tallas en quiebre).")
        else:
            st.info("No se encontraron registros procesables en el archivo maestro.")
            
    except Exception as e:
        st.error(f"⚠️ Esperando la sincronización con tu repositorio de GitHub...")
        st.info(f"Buscando el archivo plano en la ruta:\n`{URL_GITHUB_MAESTRO}`")

# PIE DE PÁGINA
st.markdown("""
    <div class="footer">
        © 2026 Gerencia Comercial Zona Occidente | KPIs Administrados por LAE. José Martín Estrada Cabrera
    </div>
    """, unsafe_allow_html=True)
