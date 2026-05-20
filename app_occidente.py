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

# --- FUNCIÓN DE ALERTA INTELIGENTE CON CRUCE REAL DE GITHUB ---
def enviar_correo_por_modificacion(df_ranking, tienda_objetivo="56"):
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
        
        # --- CRUCE 1: HISTÓRICO COMPARATIVO DESDE GITHUB ---
        pares_2025, pares_2026, dif_pares = 0, 0, 0
        if archivo_comp:
            try:
                df_op = pd.read_excel(archivo_comp) if archivo_comp.endswith('.xlsx') else pd.read_csv(archivo_comp)
                c_ano = next((c for c in df_op.columns if 'año' in c.lower() or 'ano' in c.lower()), df_op.columns[0])
                c_tda = next((c for c in df_op.columns if 'tienda' in c.lower() or 'sucursal' in c.lower()), df_op.columns[2])
                c_prs = next((c for c in df_op.columns if 'pares' in c.lower() or 'cant' in c.lower()), None)
                
                if c_prs:
                    df_op[c_tda] = df_op[c_tda].astype(str).str.strip()
                    df_filtrado = df_op[df_op[c_tda].str.contains(tienda_objetivo, na=False)]
                    res = df_filtrado.groupby(c_ano)[c_prs].sum()
                    pares_2025 = int(res.get(2025, 0))
                    pares_2026 = int(res.get(2026, 0))
                    dif_pares = pares_2025 - pares_2026
            except:
                pass

        # --- CRUCE 2: AUDITORÍA REAL CON EXTRACCIÓN DE REPOSITORIO ---
        opcion_a_sin_stock = []
        opcion_b_con_stock = []
        
        if archivo_modelos:
            try:
                df_m = pd.read_excel(archivo_modelos) if archivo_modelos.endswith('.xlsx') else pd.read_csv(archivo_modelos)
                col_m = next((c for c in df_m.columns if c.lower() in ['clave', 'modelo', 'estilo']), df_m.columns[1])
                col_p = next((c for c in df_m.columns if 'pares' in c.lower() or 'cantidad' in c.lower() or 'venta' in c.lower()), df_m.columns[2])
                col_t = next((c for c in df_m.columns if 'tienda' in c.lower() or 'sucursal' in c.lower()), df_m.columns[0])
                col_prov = next((c for c in df_m.columns if 'prov' in c.lower()), None)

                df_m = df_m[~df_m[col_t].astype(str).str.contains('3004|3015', na=False)]
                if col_prov:
                    df_m = df_m[~df_m[col_prov].astype(str).isin(['415', '426', '427'])]
                df_m = df_m[~df_m[col_m].astype(str).str.contains('BOLSA|REUSABLE', case=False, na=False)]

                # 1. El Top 20 Real Consolidad de la Zona
                top_20_zona = df_m.groupby(col_m)[col_p].sum().reset_index().sort_values(by=col_p, ascending=False).head(20)[col_m].astype(str).tolist()
                
                # 2. Qué ha vendido Plazas Outlet
                df_tienda_vta = df_m[df_m[col_t].astype(str).str.contains(tienda_objetivo, na=False)]
                modelos_vendidos_tienda = df_tienda_vta[df_tienda_vta[col_p] > 0][col_m].astype(str).unique().tolist()
                
                # 3. Modelos exitosos que están en CERO ventas en la 56
                modelos_ausentes = [mod for mod in top_20_zona if mod not in modelos_vendidos_tienda]
                
                # 4. Cruce matemático directo contra las columnas 'ex' de ventas_maestro.csv
                NOMBRE_ARCHIVO_GE = "ventas_maestro.csv"
                if os.path.exists(NOMBRE_ARCHIVO_GE):
                    df_master = pd.read_csv(NOMBRE_ARCHIVO_GE)
                    df_master.fillna(0, inplace=True)
                    df_master['Tienda'] = df_master['Tienda'].astype(int)
                    
                    # Filtramos el inventario físico de Plazas Outlet
                    df_tda_stock = df_master[df_master['Tienda'] == int(tienda_objetivo)]
                    cols_ex = [c for c in df_master.columns if c.lower().startswith('ex')]
                    
                    for mod in modelos_ausentes:
                        df_mod_stock = df_tda_stock[df_tda_stock['Modelo'].astype(str) == str(mod)]
                        stock_real_bodega = 0
                        if not df_mod_stock.empty and cols_ex:
                            stock_real_bodega = df_mod_stock[cols_ex].sum().sum()
                        
                        if stock_real_bodega > 0:
                            opcion_b_con_stock.append(mod)
                        else:
                            opcion_a_sin_stock.append(mod)
            except:
                pass

        try:
            remitente = st.secrets["CORREO_REMITENTE"]
            password = st.secrets["CORREO_PASSWORD"]
            destinatario = "fleoutgdl@divec-flexi.com"
            
            asunto = f"🚀 Desempeño Comercial y Oportunidades de Venta - Tienda {tienda_objetivo} Plazas Outlet"
            
            cuerpo = f"Estimada Ana Leticia y equipo de Plazas Outlet (Tienda {tienda_objetivo}):\n\n"
            cuerpo += "Les compartimos el análisis de resultados comerciales y de inventario de su sucursal, obtenido directamente tras la última actualización del monitor de la zona.\n\n"
            
            cuerpo += "--------------------------------------------------------------------------------\n"
            if logro_conv and logro_ticket:
                cuerpo += "🏆 ¡MUCHAS FELICIDADES POR EL RESULTADO!\n"
                cuerpo += "Queremos reconocer el extraordinario desempeño del equipo en el piso de venta. Han alcanzado y superado de forma simultánea las dos metas vitales de nuestra zona para calzado:\n"
                cuerpo += f" * Conversión Actual: {conversion_actual:.2f}% (Meta obligatoria: {meta_conv:.2f}%)\n"
                cuerpo += f" * Ticket Promedio Actual: {ticket_actual:.2f} unidades (Meta obligatoria: {meta_ticket:.2f} unidades de calzado)\n\n"
                cuerpo += "¡Excelente ritmo comercial! Mantener este nivel de enfoque asegura el éxito de la tienda y de todo el equipo. Sigan aplicando con disciplina el protocolo operativo en cada interacción.\n"
            else:
                cuerpo += "⚠️ ALERTA DE DESVIACIÓN DE METAS\n"
                cuerpo += "Es necesario ajustar la estrategia operativa en el piso de venta para alcanzar los objetivos obligatorios de calzado de la Zona Occidente:\n"
                if logro_conv:
                    cuerpo += f" ✅ CONVERSIÓN: {conversion_actual:.2f}% (Lograda, supera la meta por +{desviacion_conv:.2f}%)\n"
                else:
                    cuerpo += f" ❌ CONVERSIÓN: {conversion_actual:.2f}% (Faltan {abs(desviacion_conv):.2f}% para alcanzar la meta de {meta_conv}%)\n"
                if logro_ticket:
                    cuerpo += f" ✅ TICKET PROMEDIO: {ticket_actual:.2f} unidades (Logrado, supera la meta por +{desviacion_ticket:.2f} unidades)\n"
                else:
                    cuerpo += f" ❌ TICKET PROMEDIO: {ticket_actual:.2f} unidades (Faltan {abs(desviacion_ticket):.2f} unidades para alcanzar la meta de {meta_ticket} de calzado)\n"
                cuerpo += "\nEl equipo de liderazgo de la sucursal debe reforzar de inmediato los comportamientos clave en el piso de venta para corregir estas desviaciones antes del cierre.\n"
            cuerpo += "--------------------------------------------------------------------------------\n\n"
            
            cuerpo += "📦 PROYECCIÓN CONTRA HISTÓRICO 2025\n"
            cuerpo += "Para medir el verdadero crecimiento de la sucursal, el monitor cruzó sus cifras actuales acumuladas contra el mismo periodo del año anterior (excluyendo mermas y accesorios):\n"
            cuerpo += f" * Pares acumulados vendidos en 2025: {pares_2025:,.0f}\n"
            cuerpo += f" * Pares acumulados vendidos en 2026: {pares_2026:,.0f}\n\n"
            if dif_pares > 0:
                cuerpo += f"📉 Reto Comercial: Al día de hoy, les hace falta desplazar exactamente {dif_pares:,.0f} pares de calzado para igualar y superar el volumen histórico del año pasado. Cada cliente que cruza la puerta cuenta para cerrar esta brecha.\n\n"
            else:
                cuerpo += f"📈 ¡Excelente crecimiento! Superan el acumulado de pares del año pasado por +{abs(dif_pares):,.0f} pares de calzado desplazados.\n\n"
                
            cuerpo += "--------------------------------------------------------------------------------\n\n"
            cuerpo += "👟 AUDITORÍA DE MODELOS TOP 20 DE LA ZONA (Detección de Oportunidades Reales)\n"
            cuerpo += "El algoritmo analizó el consolidado exclusivo de los 20 modelos más vendidos en toda la Zona Occidente y detectó las siguientes situaciones en su sucursal:\n\n"
            
            cuerpo += "OPCIÓN A: Modelos Top de la Zona SIN EXISTENCIAS en su tienda\n"
            if opcion_a_sin_stock:
                for idx, mod in enumerate(opcion_a_sin_stock[:3], 1):
                    cuerpo += f" {idx}. Modelo: {mod}\n"
            else:
                cuerpo += " Sin novedades. Cuentan con existencias de todos los modelos ganadores del Top 20.\n"
                
            cuerpo += f"\nOPCIÓN B: Modelos Top de la Zona CON EXISTENCIAS pero SIN VENTAS\n"
            if opcion_b_con_stock:
                for idx, mod in enumerate(opcion_b_con_stock[:3], 1):
                    cuerpo += f" {idx}. Modelo: {mod}\n"
                cuerpo += f"\n💡 Estrategia para el equipo: Para los modelos de la Opción B, saquen el producto de la bodega de inmediato, verifiquen su correcta exhibición en las zonas calientes del piso de venta y asegúrense de que el personal lo ofrezca activamente. Son productos ganadores que les ayudarán directamente a levantar el ticket promedio y el volumen de calzado de la sucursal.\n"
            else:
                cuerpo += " Sin novedades. Todos los modelos Top con existencias registran desplazamiento en su sucursal.\n"
            
            cuerpo += "\n--------------------------------------------------------------------------------\n\n"
            cuerpo += "Agradecemos su esfuerzo diario y compromiso con los estándares de la Zona Occidente. ¡Vamos por un cierre de mes impecable!\n\n"
            cuerpo += "Atentamente,\n"
            cuerpo += "Gerencia Comercial Zona Occidente\n"
            cuerpo += "LAE. José Martín Estrada Cabrera"

            msg = MIMEText(cuerpo)
            msg['Subject'] = asunto
            msg['From'] = remitente
            msg['To'] = destinatario
            
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(remitente, password)
            server.sendmail(remitente, [destinatario], msg.as_string())
            server.quit()
            return f"✅ Correo enviado exitosamente a la Tienda 56 (Plazas Outlet) al detectar actualización del archivo."
        except Exception as e:
            return f"❌ Error al enviar el correo: {e}"
    return "❌ No se encontraron datos para la Tienda 56."

# --- DEFINICIÓN DE LAS 7 PESTAÑAS (PRESERVADAS AL 100%) ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 DESEMPEÑO COMERCIAL", 
    "📈 COMPARATIVO MENSUAL",
    "👟 TOP 20 TIENDA", 
    "🌍 TOP 20 ZONA", 
    "🧭 RUTA DEL CLIENTE",
    "🎓 CAPACITACIÓN",
    "🔄 NIVELACIÓN DE STOCK"
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

            st.table(ranking.style.apply(lambda row: ['background-color: #d4edda; color: #155724'] * 4 if row['CONVERSIÓN'] >= meta_conv and row['TICKET PROMEDIO'] >= meta_tkt else (['background-color: #fff3cd; color: #856404'] * 4 if row['CONVERSIÓN'] >= meta_conv or row['TICKET PROMEDIO'] >= meta_tkt else ['background-color: #f8d7da; color: #721c24'] * 4), axis=1).format({'CONVERSIÓN': '{:.2f}%', 'TICKET PROMEDIO': '{:.2f}'}))
            
            # --- TRIGGER AUTOMÁTICO SEGURO ---
            if "ultima_mod_detectada" not in st.session_state:
                st.session_state["ultima_mod_detectada"] = os.path.getmtime(archivo_conv)
            
            fecha_actual_archivo = os.path.getmtime(archivo_conv)
            if fecha_actual_archivo != st.session_state["ultima_mod_detectada"]:
                st.session_state["ultima_mod_detectada"] = fecha_actual_archivo
                resultado_alerta = enviar_correo_por_modificacion(ranking, tienda_objetivo="56")
                st.info(resultado_alerta)

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
                st.markdown(f"""<div class="kpi-box"><div class="kpi-title">📦 Total Pares Zona Occidente</div><div class="kpi-value">{tot_p26:,.0f} Pares</div><div class="kpi-delta" style="color: {'#155724' if var_p_global >= 0 else '#721c24'};">Variación: {"+" if var_p_global >= 0 else ""}{var_p_global:.2f}% vs 2025</div></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="kpi-box"><div class="kpi-title">💰 Total Ventas ($) Zona Occidente</div><div class="kpi-value">${tot_w26:,.2f} MXN</div><div class="kpi-delta" style="color: {'#155724' if var_w_global >= 0 else '#721c24'};">Variación: {"+" if var_w_global >= 0 else ""}{var_w_global:.2f}% vs 2025</div></div>""", unsafe_allow_html=True)
            
            st.write("<br>", unsafe_allow_html=True)
            tabla_comp = resumen[['TIENDA', 'PARES 2025', 'PARES 2026', 'VAR PARES %', 'PESOS 2025', 'PESOS 2026', 'VAR PESOS %']].sort_values(by='VAR PARES %', ascending=False).reset_index(drop=True)
            st.table(tabla_comp.style.map(lambda val: f"background-color: {'#d4edda' if val >= 0 else '#f8d7da'}; color: {'#155724' if val >= 0 else '#721c24'}; font-weight: bold;" if isinstance(val, (int, float)) else '', subset=['VAR PARES %', 'VAR PESOS %']).format({'PARES 2025': '{:,.0f}', 'PARES 2026': '{:,.0f}', 'VAR PARES %': '{:+.2f}%', 'PESOS 2025': '${:,.2f}', 'PESOS 2026': '${:,.2f}', 'VAR PESOS %': '{:+.2f}%'}))

# --- PESTAÑAS 3 Y 4: RANKINGS ---
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

    with tab3:
        t_sel = st.selectbox("Selecciona Tienda:", sorted(df_m[col_t].unique()))
        top_t = df_m[df_m[col_t] == t_sel].groupby(col_m)[col_p].sum().reset_index().sort_values(by=col_p, ascending=False).head(20).reset_index(drop=True)
        top_t.columns = ['MODELO', 'PARES VENDIDOS']
        st.table(top_t.style.apply(lambda d: pd.DataFrame('background-color: #d1e7dd; color: #0f5132; font-weight: bold', index=d.index, columns=d.columns).iloc[5:, :].apply(lambda x: ''), axis=None))

    with tab4:
        st.subheader("🌍 Consolidado Zona Occidente")
        top_z = df_m.groupby(col_m)[col_p].sum().reset_index().sort_values(by=col_p, ascending=False).head(20).reset_index(drop=True)
        top_z.columns = ['MODELO', 'PARES VENDIDOS']
        st.table(top_z.style.apply(lambda d: pd.DataFrame('background-color: #d1e7dd; color: #0f5132; font-weight: bold', index=d.index, columns=d.columns).iloc[5:, :].apply(lambda x: ''), axis=None))

# --- PESTAÑA 5: RUTA DEL CLIENTE ---
with tab5:
    st.subheader("🧭 Protocolo Operativo en Piso de Venta")
    if os.path.exists("RC Zona Occidente.png"): st.image("RC Zona Occidente.png", use_container_width=True)

# --- PESTAÑA 6: PORTAL DE CAPACITACIÓN Y MANUAL DE INTEGRACIÓN ---
with tab6:
    st.markdown("## 🎓 Centro de Capacitación y Desarrollo Operativo")
    col_izq, col_der = st.columns([1, 1])
    with col_izq:
        st.markdown("### 📹 Videos de Capacitación para el Personal")
        opciones_video = {"Mi Nómina Flexi": "https://youtu.be/688Bi49rI30", "Tutorial Vales de Zapatos": "https://youtu.be/6hB95lYcL1g", "Tutorial mi Flexi": "https://youtu.be/WVi8geGSeOg"}
        video_seleccionado = st.selectbox("Selecciona el material audiovisual a reproducir:", list(opciones_video.keys()))
        st.video(opciones_video[video_seleccionado])
        
    with col_der:
        st.markdown("### 📘 Manual de Integración a Tiendas Flexi")
        with st.expander("🎯 1. PROPÓSITO DEL MONITOR COMERCIAL"):
            st.markdown("Monitor interactivo desarrollado bajo la dirección del **LAE. José Martín Estrada Cabrera**.\n* 👟 **Ticket Promedio:** Meta de 1.29 unidades (exclusivamente calzado).\n* 📊 **Conversión Mínima:** Meta de 10.90% en el piso de venta.")
        with st.expander("📝 2. OBJETIVO DEL MANUAL Y FILOSOFÍA"):
            st.markdown("**Plan de Retención de Personal**\n\nEstablecer un proceso de acogida estandarizado que reduzca la rotación en los primeros 90 días, transformando la incorporación en una experiencia de bienvenida profesional y humana.")
        with st.expander("🤝 3. PILAR I: BIENVENIDA (LOGÍSTICA Y ORDEN)"):
            st.markdown("**Concepto:** Proyectar orden.\n**La Acción:** Asegurarse de que el espacio físico esté impecable, las herramientas configuradas y el uniforme de la talla correcta listo antes de que el colaborador ingrese.")
        with st.expander("👥 4. PILAR II: ACOMPAÑAMIENTO (MENTORÍA)"):
            st.markdown("**Concepto:** Eliminar la 'soledad del novato' mediante el sistema de compañero guía.\n**La Acción:** Designar a un mentor con experiencia y actitud positiva la primera semana.")
        with st.expander("🧭 5. PILAR III: CLARIDAD DEL PROPÓSITO (KPIs)"):
            st.markdown("Conectar tareas diarias con el impacto real en la zona. Todo colaborador debe cuidar las metas vitales de calzado:\n* 👟 **Ticket Promedio:** Meta de 1.29 unidades.\n* 📊 **Conversión:** Meta de 10.90% en piso de venta.")
        with st.expander("📈 6. PILAR IV: METAS DE CORTO PLAZO"):
            st.markdown("Brindar claridad absoluta sobre expectativas. Establecer objetivos específicos para la primera semana, los primeros 15 días y el primer mes, dando retroalimentación al finalizar cada etapa.")
        with st.expander("🎉 7. PILAR V: VINCULACIÓN SOCIAL"):
            st.markdown("Humanizar el entorno laboral. Organizar momentos de convivencia donde el equipo reciba formalmente al nuevo integrante. El sentido de pertenencia es el factor de retención más potente.")

# --- PESTAÑA 7: NIVELACIÓN ---
with tab7:
    st.subheader("🔄 Algoritmo Maestro de Nivelación de Inventarios (2 Meses)")
    st.info("Pestaña congelada y en fase de análisis estructural bajo las nuevas directrices lógicas (Candado origen, quiebre absoluto y proximidad).")

st.markdown("""<div class="footer">© 2026 Gerencia Comercial Zona Occidente | KPIs Administrados por LAE. José Martín Estrada Cabrera</div>""", unsafe_allow_html=True)
