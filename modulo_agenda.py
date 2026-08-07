import streamlit as st
import pandas as pd
import datetime
import urllib.parse
import re

def mostrar_modulo_agenda(client_gs):
    st.markdown("<h2 style='color: #4338ca;'>📓 Agenda de Clientes y Recuperación de Ventas</h2>", unsafe_allow_html=True)
    st.write("Registra clientes con tallas agotadas y recibe alertas automáticas cuando el calzado ingrese a bodega.")

    # Conectar a la pestaña de Google Sheets
    try:
        archivo = client_gs.open_by_key('1lGlVEBgu9QsrH9PYTTuoRKQeWnYiR7OwUElCsfkDgoM')
        sheet_agenda = archivo.worksheet('Agenda_Clientes')
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets (Asegúrate de haber creado la pestaña 'Agenda_Clientes'). Detalles: {e}")
        return

    # Pestañas internas del módulo
    tab_alertas, tab_registro = st.tabs(["🚨 Panel de Alertas y Seguimiento", "📝 Nuevo Registro en Piso"])

    # ==========================================
    # TAB 1: PANEL DE ALERTAS Y SEGUIMIENTO
    # ==========================================
    with tab_alertas:
        st.markdown("### 🔔 Clientes en Espera")
        
        # Obtener datos de la nube
        datos = sheet_agenda.get_all_values()
        if len(datos) > 1:
            df_agenda = pd.DataFrame(datos[1:], columns=datos[0])
            # Filtrar solo los que están pendientes
            df_pendientes = df_agenda[df_agenda['Estatus'].astype(str).str.upper() != 'CONTACTADO'].copy()
            
            if df_pendientes.empty:
                st.success("✨ ¡Excelente! No hay clientes en lista de espera sin contactar.")
            else:
                # Mostrar tarjetas para cada cliente pendiente
                for idx, row in df_pendientes.iterrows():
                    cliente = row.get('Cliente', 'Sin Nombre')
                    whatsapp = row.get('WhatsApp', '')
                    modelo = row.get('Modelo', '').upper()
                    talla = row.get('Talla', '')
                    sucursal = row.get('Sucursal', '')
                    fecha = row.get('Fecha', '')
                    
                    # Generar mensaje de WhatsApp predefinido
                    mensaje = f"Hola {cliente}, te saludamos de Flexi {sucursal}. Te informamos que el modelo {modelo} en talla {talla} que buscabas ya está disponible. ¿Te lo apartamos?"
                    mensaje_url = urllib.parse.quote(mensaje)
                    link_wa = f"https://wa.me/52{whatsapp}?text={mensaje_url}" if whatsapp else "#"
                    
                    # Diseño de tarjeta
                    st.markdown(f"""
                    <div style="background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 5px solid #E30613; margin-bottom: 15px;">
                        <h4 style="color: white; margin-top: 0;">👤 {cliente} - <span style="color: #fbbf24;">{sucursal}</span></h4>
                        <p style="color: #94a3b8; margin: 5px 0;"><strong>Modelo:</strong> {modelo} | <strong>Talla:</strong> {talla} | <strong>Fecha:</strong> {fecha}</p>
                        <a href="{link_wa}" target="_blank" style="text-decoration: none;">
                            <button style="background-color: #25D366; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; margin-top: 10px;">
                                💬 Enviar WhatsApp
                            </button>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Aún no hay clientes registrados en la agenda.")

    # ==========================================
    # TAB 2: FORMULARIO DE REGISTRO
    # ==========================================
    with tab_registro:
        st.markdown("### 📝 Captura de Datos en Caja")
        with st.form("form_nuevo_cliente"):
            col1, col2 = st.columns(2)
            
            with col1:
                sucursal_input = st.text_input("🏢 Sucursal (Ej. 56 Plazas Outlet):")
                cliente_input = st.text_input("👤 Nombre del Cliente:")
                whatsapp_input = st.text_input("📱 WhatsApp (10 dígitos):", max_chars=10)
            
            with col2:
                modelo_input = st.text_input("👟 Modelo Buscado:")
                talla_input = st.number_input("📏 Talla (Ej. 25.0):", min_value=10.0, max_value=35.0, step=0.5, value=25.0)
                notas_input = st.text_area("📝 Notas (Opcional):", height=68)
            
            btn_guardar = st.form_submit_button("💾 Guardar Cliente", type="primary")
            
            if btn_guardar:
                if not sucursal_input or not cliente_input or not modelo_input:
                    st.error("⚠️ Faltan datos obligatorios (Sucursal, Cliente y Modelo).")
                elif len(whatsapp_input) < 10 or not whatsapp_input.isdigit():
                    st.error("⚠️ El número de WhatsApp debe tener 10 dígitos numéricos.")
                else:
                    # Preparar datos para Google Sheets
                    fecha_hoy = (datetime.datetime.utcnow() - datetime.timedelta(hours=6)).strftime("%d/%m/%Y")
                    fila_nueva = [
                        fecha_hoy, sucursal_input, cliente_input, whatsapp_input, 
                        modelo_input.upper(), str(talla_input), notas_input, "ESPERANDO"
                    ]
                    
                    try:
                        sheet_agenda.append_row(fila_nueva)
                        st.success(f"✅ ¡Cliente {cliente_input} registrado exitosamente! El sistema avisará cuando llegue su talla.")
                    except Exception as e:
                        st.error(f"❌ Error al guardar en la nube: {e}")
