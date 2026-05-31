import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
import datetime
from fpdf import FPDF
import openpyxl
# --- FUNCIONES DE BITÁCORA (FINAL) ---
def cargar_tiendas():
    nombre_archivo = "CORREO DE TIENDAS.xlsx"
    try:
        # Usamos read_excel porque su archivo es .xlsx
        return pd.read_excel(nombre_archivo)
    except Exception as e:
        st.error(f"Error al cargar el archivo de Excel '{nombre_archivo}': {e}")
        return pd.DataFrame({'NOMBRE': ['Error'], 'ENCARGADO': ['Sin datos']})

def guardar_incidencia(datos):
    archivo_csv = "bitacora_incidencias.csv"
    df_nuevo = pd.DataFrame([datos])
    if not os.path.exists(archivo_csv):
        df_nuevo.to_csv(archivo_csv, index=False)
    else:
        df_nuevo.to_csv(archivo_csv, mode='a', header=False, index=False)
# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Monitor Comercial Flexi Occidente", layout="wide")

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
    <h1 class="main-title">🔴 MONITOR COMERCIAL FLEXI OCCIDENTE</h1>
    """, unsafe_allow_html=True)

def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith(('.xlsx', '.csv'))]
    return sorted(archivos)[-1] if archivos else None

archivo_conv = buscar_archivo('Conversion')
archivo_modelos = buscar_archivo('Venta_Modelos')
archivo_comp = buscar_archivo('Comparativo por Operacion')
# --- 1. EL CARTERO LIGERO (NUEVO ENFOQUE: COMPARATIVO MENSUAL) ---
def enviar_correo_ejecutivo(tienda_objetivo, conversion, ticket, meta_conv, meta_tkt, faltan_pares, faltan_pesos):
    
    # 1. Evaluamos el cumplimiento de las metas esenciales de calzado
    logro_conv = conversion >= meta_conv
    logro_ticket = ticket >= meta_tkt
    desviacion_conv = conversion - meta_conv
    desviacion_ticket = ticket - meta_tkt

    # 2. Redacción directa y enfocada en los indicadores de piso de venta y comparativo
    try:
        remitente = st.secrets["CORREO_REMITENTE"]
        password = st.secrets["CORREO_PASSWORD"]
        destinatario = "fleoutgdl@divec-flexi.com" 
        
        asunto = f"🚀 Desempeño Comercial y Reto Acumulado - Tienda {tienda_objetivo}"
        
        cuerpo = f"Estimada Lety y equipo de la Tienda {tienda_objetivo}:\n\n"
        cuerpo += "Les compartimos el análisis de resultados comerciales de su sucursal, obtenido directamente tras la última actualización del monitor.\n\n"
        
        cuerpo += "--------------------------------------------------------------------------------\n"
        if logro_conv and logro_ticket:
            cuerpo += "🏆 ¡MUCHAS FELICIDADES POR EL RESULTADO!\n"
            cuerpo += "Queremos reconocer el extraordinario desempeño del equipo en el piso de venta. Han alcanzado y superado de forma simultánea las dos metas vitales de nuestra zona para calzado:\n"
            cuerpo += f" * Conversión Actual: {conversion:.2f}% (Meta obligatoria: {meta_conv:.2f}%)\n"
            cuerpo += f" * Ticket Promedio Actual: {ticket:.2f} unidades (Meta obligatoria: {meta_tkt:.2f} unidades de calzado)\n\n"
        else:
            cuerpo += "⚠️ ALERTA DE DESVIACIÓN DE METAS EN PISO DE VENTA\n"
            cuerpo += "Es necesario ajustar la estrategia operativa para alcanzar los objetivos obligatorios de la Zona Occidente:\n"
            if logro_conv:
                cuerpo += f" ✅ CONVERSIÓN: {conversion:.2f}% (Lograda)\n"
            else:
                cuerpo += f" ❌ CONVERSIÓN: {conversion:.2f}% (Faltan {abs(desviacion_conv):.2f}% para alcanzar la meta de {meta_conv}%)\n"
            if logro_ticket:
                cuerpo += f" ✅ TICKET PROMEDIO: {ticket:.2f} unidades (Logrado)\n"
            else:
                cuerpo += f" ❌ TICKET PROMEDIO: {ticket:.2f} unidades (Faltan {abs(desviacion_ticket):.2f} unidades para alcanzar la meta de {meta_tkt})\n\n"
        
        cuerpo += "--------------------------------------------------------------------------------\n"
        cuerpo += "📊 ANÁLISIS COMPARATIVO MENSUAL (RETO ACUMULADO)\n"
        cuerpo += "Para igualar y superar el comparativo histórico del año pasado, al día de hoy el estatus es el siguiente:\n\n"
        
        if faltan_pares > 0:
            cuerpo += f" 👟 Te faltan: {faltan_pares:,.0f} pares de calzado.\n"
        else:
            cuerpo += f" 👟 Llevas a favor: {abs(faltan_pares):,.0f} pares de calzado.\n"
            
        if faltan_pesos > 0:
            cuerpo += f" 💰 Te faltan: ${faltan_pesos:,.2f} MXN en importe.\n\n"
        else:
            cuerpo += f" 💰 Llevas a favor: ${abs(faltan_pesos):,.2f} MXN en importe.\n\n"
        
        cuerpo += "¡Cada cliente que cruza la puerta cuenta para superar esta marca! Éxito en sus ventas.\n"
        cuerpo += "--------------------------------------------------------------------------------\n\n"
        
        cuerpo += "Atentamente,\n"
        cuerpo += "Gerencia Comercial Zona Occidente\n"
        cuerpo += "LAE. José Martín Estrada Cabrera"

        # 3. Envío seguro a través del servidor
        msg = MIMEText(cuerpo)
        msg['Subject'] = asunto
        msg['From'] = remitente
        msg['To'] = destinatario
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(remitente, password)
        server.sendmail(remitente, [destinatario], msg.as_string())
        server.quit()
        return f"✅ Correo ejecutivo enviado exitosamente a la Tienda {tienda_objetivo}."
    except Exception as e:
        return f"❌ Error al enviar el correo a la Tienda {tienda_objetivo}: {e}"
# --- GENERADOR DEL REPORTE TOP 20 EN PDF ---
def generar_reporte_top20_pdf(df_top20, nombre_sucursal):
    # Ajuste de reloj para la Zona Occidente (UTC - 6 horas)
    hora_mexico = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    fecha_actual = hora_mexico.strftime("%d/%m/%Y")    
    # Configuración de hoja tamaño Carta
    pdf = FPDF(orientation='P', unit='mm', format='Letter')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # 1. ENCABEZADO INSTITUCIONAL
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(227, 6, 19) # Rojo Flexi
    pdf.cell(0, 8, "FLEXI - ZONA OCCIDENTE", ln=True, align="C")
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 8, "AUDITORIA COMERCIAL: TOP 20 MODELOS DE LA SUCURSAL", ln=True, align="C")
    pdf.line(10, 28, 205, 28)
    pdf.ln(8)
    
    # 2. DATOS DE LA SUCURSAL
    pdf.set_font("Arial", '', 10)
    pdf.cell(40, 6, "Fecha de Reporte:", 0, 0)
    pdf.cell(60, 6, fecha_actual, 0, 0)
    pdf.cell(35, 6, "Encargada:", 0, 0)
    pdf.cell(60, 6, "_______________________", 0, 1)
    
    pdf.cell(40, 6, "Sucursal:", 0, 0)
    pdf.cell(60, 6, nombre_sucursal, 0, 0)
    pdf.cell(35, 6, "Gerente Comercial:", 0, 0)
    pdf.cell(60, 6, "LAE. Jose Martin Estrada Cabrera", 0, 1)
    pdf.ln(8)
    
    # 3. ENCABEZADO DE LA TABLA
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(227, 6, 19)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(15, 8, "#", 1, 0, 'C', fill=True)
    pdf.cell(30, 8, "MODELO", 1, 0, 'C', fill=True)
    pdf.cell(40, 8, "PARES VENDIDOS", 1, 0, 'C', fill=True)
    pdf.cell(110, 8, "DESEMPENO EN LA ZONA OCCIDENTE", 1, 1, 'C', fill=True)
    
    # 4. LLENADO DE DATOS
    pdf.set_font("Arial", '', 9)
    pdf.set_text_color(0, 0, 0)
    for i, row in df_top20.iterrows():
        posicion = i + 1
        modelo = str(row.get('MODELO', 'S/D'))
        pares = str(row.get('PARES VENDIDOS', '0'))
        
        if posicion <= 5: desempeno = "Top 5 mas vendido en la region"
        elif posicion <= 10: desempeno = "Alta demanda en la zona"
        else: desempeno = "Desplazamiento regular"
            
        pdf.cell(15, 7, f"{posicion:02d}", 1, 0, 'C')
        pdf.cell(30, 7, modelo, 1, 0, 'C')
        pdf.cell(40, 7, pares, 1, 0, 'C')
        pdf.cell(110, 7, desempeno, 1, 1, 'L')
        
    pdf.ln(10)
    
    # 5. FIRMAS
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, "Nota: Este documento sirve como guia visual para que el equipo en piso valide fisicamente en su bodega que estos modelos ganadores esten exhibidos.")
    pdf.ln(25)
    
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(90, 5, "_______________________", 0, 0, 'C')
    pdf.cell(15, 5, "", 0, 0)
    pdf.cell(90, 5, "_______________________", 0, 1, 'C')
    
    pdf.cell(90, 5, "Firma de la Encargada", 0, 0, 'C')
    pdf.cell(15, 5, "", 0, 0)
    pdf.cell(90, 5, "LAE. Jose Martin Estrada", 0, 1, 'C')
    
    pdf.cell(90, 5, "Responsable de Sucursal", 0, 0, 'C')
    pdf.cell(15, 5, "", 0, 0)
    pdf.cell(90, 5, "Gerente Comercial", 0, 1, 'C')
    
    return bytes(pdf.output(dest='S').encode('latin1'))
    # --- DEFINICIÓN DE LAS 8 PESTAÑAS ---
tab1, tab2, tab3, tab4, tab_bitacora, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 DESEMPEÑO COMERCIAL", 
    "📈 COMPARATIVO MENSUAL",
    "👟 TOP 20 TIENDA", 
    "🌍 TOP 20 ZONA", 
    "📝 BITÁCORA", 
    "🧭 RUTA DEL CLIENTE", 
    "🎓 CAPACITACIÓN", 
    "🔄 NIVELACIÓN DE STOCK", 
    "🎯 MONITOR ESTRATÉGICO"
])
# ========================================================
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
            
# --- PESTAÑA 2: COMPARATIVO MENSUAL ---
with tab2:
    if archivo_comp:
        st.subheader("📊 Análisis Comparativo de Calzado Mensual")
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
            # --- 3. BOTÓN DE ENVÍO MANUAL (PROTEGIDO POR CLAVE) ---
            st.write("<br>", unsafe_allow_html=True)
            st.markdown("---")
            
            # Creamos dos columnas para colocar el cuadro de texto y el botón alineados
            col_clave, col_boton = st.columns([1, 2])
            
            with col_clave:
                password_input = st.text_input("Clave de autorización", type="password")
            
            with col_boton:
                st.write("<br>", unsafe_allow_html=True) # Alineación visual con el cuadro de texto
                if st.button("🚀 Enviar Reporte Ejecutivo del Día (Tienda 56)", type="primary"):
                    # Validación estricta de la clave asignada para la zona
                    if password_input == "T5604b":
                        tienda_obj = "56"
                        conv_actual = 0.0
                        tkt_actual = 0.0
                        
                        # 1. Extraemos Conversión y Ticket del archivo de Conversión
                        if archivo_conv:
                            try:
                                df_c = pd.read_excel(archivo_conv) if archivo_conv.endswith('.xlsx') else pd.read_csv(archivo_conv)
                                df_c = df_c[~df_c.iloc[:,0].astype(str).str.contains('3004|3015|Total|TOTAL|Resumen', na=False)]
                                col_tda_c = next((c for c in df_c.columns if 'Tienda' in c or 'TIENDA' in c), df_c.columns[0])
                                col_conv_real = next((c for c in df_c.columns if 'Conv' in c and 'Actual' in c), None)
                                col_tkt_real = next((c for c in df_c.columns if 'Ticket' in c or 'Uds/Tkt' in c or 'Prom' in c), None)
                                
                                df_c['CONVERSIÓN'] = df_c[col_conv_real].apply(lambda x: x*100 if x < 1 else x)
                                df_c['TICKET PROMEDIO'] = df_c[col_tkt_real]
                                
                                fila_c = df_c[df_c[col_tda_c].astype(str).str.contains(tienda_obj, na=False)]
                                if not fila_c.empty:
                                    conv_actual = float(fila_c.iloc[0]['CONVERSIÓN'])
                                    tkt_actual = float(fila_c.iloc[0]['TICKET PROMEDIO'])
                            except:
                                pass

                        # 2. Extraemos el Reto en Pares y Pesos con filtros aplicados de calzado puro
                        faltan_pares_calc = 0
                        faltan_pesos_calc = 0.0
                        
                        if archivo_comp:
                            try:
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
                                        
                                    df_filtrado = df_op[df_op[c_tda].str.contains(tienda_obj, na=False)]
                                    res = df_filtrado.groupby(c_ano)[[c_prs, c_imp]].sum()
                                    
                                    pares_2025 = int(res.get(c_prs).get(2025, 0))
                                    pares_2026 = int(res.get(c_prs).get(2026, 0))
                                    pesos_2025 = float(res.get(c_imp).get(2025, 0.0))
                                    pesos_2026 = float(res.get(c_imp).get(2026, 0.0))
                                    
                                    faltan_pares_calc = pares_2025 - pares_2026
                                    faltan_pesos_calc = pesos_2025 - pesos_2026
                            except:
                                pass
                        
                        # 3. Disparador seguro del correo ejecutivo
                        with st.spinner("Enviando reporte ejecutivo..."):
                            resultado_alerta = enviar_correo_ejecutivo(
                                tienda_objetivo=tienda_obj, 
                                conversion=conv_actual, 
                                ticket=tkt_actual, 
                                meta_conv=10.9, 
                                meta_tkt=1.29, 
                                faltan_pares=faltan_pares_calc, 
                                faltan_pesos=faltan_pesos_calc
                            )
                        
                        if resultado_alerta:
                            if "✅" in resultado_alerta: st.success(resultado_alerta)
                            else: st.error(resultado_alerta)
                    else:
                        st.error("❌ Clave incorrecta. Acceso denegado para el envío.")
# --- PESTAÑAS 3 Y 4: DESPLIEGUE DE RANKINGS DE MODELOS ---
if archivo_modelos:
    df_m = pd.read_excel(archivo_modelos) if archivo_modelos.endswith('.xlsx') else pd.read_csv(archivo_modelos)
    col_m = next((c for c in df_m.columns if c.lower() in ['clave', 'modelo', 'estilo']), df_m.columns[1])
    col_p = next((c for c in df_m.columns if 'pares' in c.lower() or 'cantidad' in c.lower() or 'venta' in c.lower()), df_m.columns[2])
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

        # --- BOTÓN DE DESCARGA DE REPORTE EN PDF ---
        pdf_bytes = generar_reporte_top20_pdf(
            df_top20=top_t, 
            nombre_sucursal=str(t_sel)
        )

        st.write("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📄 Descargar Formato de Auditoría (PDF Oficial)",
            data=pdf_bytes,
            file_name=f"Auditoria_Top20_{t_sel}.pdf",
            mime="application/pdf",
            type="primary"
        )

    with tab4:
        st.subheader("🌍 Consolidado Zona Occidente")
        df_z = df_m.groupby(col_m)[col_p].sum().reset_index()
        top_z = df_z.sort_values(by=col_p, ascending=False).head(20).reset_index(drop=True)
        top_z.columns = ['MODELO', 'PARES VENDIDOS']
        st.table(top_z.style.apply(resaltar_top_5, axis=None))
        # --- CONTENIDO DE LA PESTAÑA BITÁCORA ---
with tab_bitacora:
    st.subheader("📝 Registro de Incidencias Operativas")
    df_tiendas = cargar_tiendas()
    
    # 1. Selección de tienda reactiva
    tienda_seleccionada = st.selectbox("Selecciona la Tienda:", df_tiendas['NOMBRE'].unique())
    
    # 2. Búsqueda y visualización INMEDIATA del encargado
    fila_tienda = df_tiendas[df_tiendas['NOMBRE'] == tienda_seleccionada]
    if not fila_tienda.empty:
        encargado_actual = fila_tienda['ENCARGADO'].values[0]
        st.info(f"**Encargado(a) detectado(a):** {encargado_actual}")
    else:
        encargado_actual = "No encontrado"
        st.warning(f"**Encargado(a):** {encargado_actual}")
        
    # 3. Datos de la incidencia (con fecha corregida)
    fecha_mexico = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    fecha = st.date_input("Fecha", fecha_mexico.date())
    factor = st.selectbox("Factor Principal:", [
        "👟 Faltante de Tallas (Proyecto Tallas Extremas)",
        "🌧️ Clima adverso", 
        "📉 Bajo tráfico atípico", 
        "🧑‍🤝‍🧑 Plantilla incompleta", 
        "🔌 Falla: VPN FortiClient", 
        "💻 Falla: Sistema/Terminales", 
        "🚧 Afectación de acceso", 
        "🎉 Factor externo"
    ])
    notas = st.text_area("Detalles adicionales:")
    
    # 4. Botón de guardado
    if st.button("💾 Guardar en Bitácora"):
        datos = {
            "Fecha": str(fecha),
            "Tienda": tienda_seleccionada,
            "Encargado": encargado_actual,
            "Factor": factor,
            "Notas": notas
        }
        guardar_incidencia(datos)
        st.success(f"✅ Incidencia registrada para {tienda_seleccionada}")

# --- PESTAÑA 5: RUTA DEL CLIENTE ---
with tab5:
    st.subheader("🧭 Protocolo Operativo en Piso de Venta")
    nombre_imagen = "RC Zona Occidente.png"
    if os.path.exists(nombre_imagen):
        st.image(nombre_imagen, use_container_width=True)
    else:
        st.warning("⚠️ La imagen 'RC Zona Occidente.png' aún no se encuentra en GitHub.")

# --- PESTAÑA 6: PORTAL DE CAPACITACIÓN Y MANUAL DE INTEGRACIÓN RECONSTRUIDO AL 100% ---
with tab6:
    st.markdown("## 🎓 Centro de Capacitación y Desarrollo Operativo")
    st.write("Bienvenido al espacio interactivo para el fortalecimiento del sentido de pertenencia y alineación comercial de la Zona Occidente.")
    
    col_izq, col_der = st.columns([1, 1])
    
    with col_izq:
        st.markdown("### 📹 Videos de Capacitación para el Personal")
        opciones_video = {
            "Mi Nómina Flexi": "https://youtu.be/688Bi49rI30",
            "Tutorial Vales de Zapatos": "https://youtu.be/6hB95lYcL1g",
            "Tutorial mi Flexi": "https://youtu.be/WVi8geGSeOg"
        }
        
        video_seleccionado = st.selectbox("Selecciona el material audiovisual a reproducir:", list(opciones_video.keys()))
        url_video = opciones_video[video_seleccionado]
        
        st.write("<br>", unsafe_allow_html=True)
        st.video(url_video)
        st.link_button(f"🚀 Clic aquí para ver {video_seleccionado} directo en YouTube", url_video, type="primary")
        
    with col_der:
        st.markdown("### 📘 Manual de Integración a Tiendas Flexi")
        
        with st.expander("🎯 1. PROPÓSITO DEL MONITOR COMERCIAL"):
            st.markdown("""
            Este monitor interactivo fue desarrollado bajo la dirección del **LAE. José Martín Estrada Cabrera** con el objetivo de centralizar, automatizar y auditar los indicadores comerciales clave de las tiendas de la Zona Occidente.
            
            **Metas Estratégicas de la Zona:**
            * 👟 **Ticket Promedio:** Meta de 1.29 unidades (enfocado exclusivamente en calzado).
            * 📊 **Conversión Mínima:** Meta de 10.90% en el piso de venta.
            """)
            
        with st.expander("📝 2. OBJETIVO DEL MANUAL Y FILOSOFÍA"):
            st.markdown("""
            **Plan de Retención de Personal y Fortalecimiento del Sentido de Pertenencia**
            
            **Objetivo General:**
            Establecer un proceso de acogida estandarizado que reduzca la rotación de personal en los primeros 90 días, transformando la incorporación en una experiencia de bienvenida profesional y humana.
            
            *La permanencia del personal de nueva contratación no depende únicamente de las condiciones laborales, sino de la calidad de su integración inicial. Este espacio presenta los pilares fundamentales para asegurar que el nuevo colaborador se sientan valorado, guiado y conectado con los objetivos de la organización desde su primer día.*
            """)
            
        with st.expander("🤝 3. PILAR I: BIENVENIDA (LOGÍSTICA Y ORDEN)"):
            st.markdown("""
            **Concepto:** Proyectar orden y profesionalismo. La preparación del entorno de trabajo es el primer mensaje que el colaborador recibe sobre la cultura de la empresa.
            
            **La Acción:** Asegurarse de que el espacio físico esté impecable, las herramientas de trabajo (computadora, accesos, sistemas) estén configuradas y el uniforme de la talla correcta esté listo sobre su lugar antes de que el colaborador cruce la puerta (en la medida de lo posible).
            
            **El Impacto:** Elimina la ansiedad e incertidumbre del primer día. Comunica de forma implícita: "Te estábamos esperando y tu llegada es importante para nosotros".
            """)
            
        with st.expander("👥 4. PILAR II: ACOMPAÑAMIENTO (MENTORÍA)"):
            st.markdown("""
            **Concepto:** Eliminar la "soledad del novato" mediante el sistema de compañero guía.
            
            **La Acción:** Designar a un colaborador con experiencia y actitud positiva para que actúe como mentor durante la primera semana.
            """)
            
        with st.expander("🧭 5. PILAR III: CLARIDAD DEL PROPÓSITO (KPIs)"):
            st.markdown("""
            **Concepto:** Conectar las tareas diarias con el impacto real en el éxito de la zona y la misión de la empresa. Genera compromiso emocional. Un colaborador que encuentra propósito en su trabajo desarrolla una lealtad que va más allá de la oferta económica.
            
            **Enfoque Comercial Zona Occidente:**
            Todo colaborador de nuevo ingreso debe comprender que cuidamos con excelencia comercial dos indicadores vitales de calzado:
            * 👟 **Ticket Promedio:** Meta de 1.29 unidades por ticket.
            * 📊 **Conversión:** Meta de 10.90% en piso de venta.
            """)
            
        with st.expander("📈 6. PILAR IV: METAS DE CORTO PLAZO"):
            st.markdown("""
            **Concepto:** Brindar claridad absoluta sobre las expectativas de desempeño en la etapa crítica.
            
            **La Acción:** Establecer objetivos específicos, medibles y alcanzables para la primera semana, los primeros 15 días y el primer mes. Brindar retroalimentación constructiva al finalizar cada etapa.
            
            **El Impacto:** Reduce la frustración causada por la ambigüedad. Permite que el colaborador celebre victorias tempranas y desarrolle la autoconfianza necesaria para su profesionalización.
            """)
            
        with st.expander("🎉 7. PILAR V: VINCULACIÓN SOCIAL"):
            st.markdown("""
            **Concepto:** Humanizar el entorno laboral y fomentar la integración grupal.
            
            **La Acción:** Organizar activamente momentos de convivencia (como una dinámica de presentación) donde el equipo actual reciba formalmente al nuevo integrante.
            
            **El Impacto:** Rompe las barreras invisibles entre el personal antiguo y el nuevo. El sentido de pertenencia a un grupo social es el factor de retención más potente ante ofertas de la competencia.
            
            ---
            *Nota Final: La integración no termina al finalizar el primer día; es un proceso continuo de acompañamiento. El éxito de este manual reside en la consistencia con la que el liderazgo de la tienda aplique cada uno de estos puntos con cada nuevo integrante.*
            """)

# --- PESTAÑA 7: INVENTARIOS CONGELADA PARA ANALISIS ---
with tab7:
    st.subheader("🔄 Algoritmo Maestro de Nivelación de Inventarios (2 Meses)")
    st.info("Pestaña congelada y en fase de análisis estructural bajo las nuevas directrices lógicas (Candado origen, quiebre absoluto y proximidad).")
# --- PESTAÑA 8: MONITOR ESTRATÉGICO ---
with tab8:
    st.header("🎯 MONITOR ESTRATÉGICO")
    
    # Botón de diagnóstico de conexión
    if st.button("Verificar Conexión y Cargar Datos"):
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            
            # Carga de credenciales
            creds_dict = dict(st.secrets["gcp_service_account"])
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            
            # Intento de apertura por nombre
            archivo = client.open('Monitor Comercial Flexi-Datos')
            sheet = archivo.get_worksheet(0)
            datos = sheet.get_all_values()
            
            if datos:
                st.success("✅ ¡Conexión establecida y datos cargados!")
                df_monitor = pd.DataFrame(datos[1:], columns=datos[0])
                st.dataframe(df_monitor, use_container_width=True)
            else:
                st.warning("La hoja está conectada pero vacía.")
                
        except gspread.exceptions.SpreadsheetNotFound:
            st.error("❌ Error: No se encontró el archivo 'Monitor Comercial Flexi Occidente'. Verifica que el nombre sea exacto.")
        except Exception as e:
            st.error(f"❌ Error de conexión: {e}")
            st.info("Nota: Asegúrate de que el correo del robot sea 'Editor' en el archivo.")    
# PIE DE PÁGINA
st.markdown("""
    <div class="footer">
        © 2026 Gerencia Comercial Zona Occidente | KPIs Administrados por LAE. José Martín Estrada Cabrera
    </div>
    """, unsafe_allow_html=True)
