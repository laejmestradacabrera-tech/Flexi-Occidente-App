import streamlit as st
import pandas as pd
import datetime
import urllib.parse
import os

def cargar_nombres_tiendas():
    """Función que lee automáticamente el archivo de tiendas real del monitor"""
    archivos = [f for f in os.listdir('.') if 'CORREO DE TIENDAS' in f.upper() and f.endswith(('.xlsx', '.csv'))]
    if archivos:
        archivo = sorted(archivos)[-1]
        try:
            df = pd.read_excel(archivo) if archivo.endswith('.xlsx') else pd.read_csv(archivo)
            # Normalizamos columnas y buscamos la columna NOMBRE
            df.columns = df.columns.astype(str).str.strip().str.upper()
            col_nom = 'NOMBRE' if 'NOMBRE' in df.columns else df.columns[1]
            nombres = df[col_nom].dropna().astype(str).unique().tolist()
            # Retornamos la lista ordenada alfabéticamente excluyendo espacios vacíos
            return sorted([n for n in nombres if n.strip() != ''])
        except Exception:
            pass
    return ["Sin Sucursales Cargadas"]

def mostrar_modulo_agenda(client_gs):
    st.markdown("<h2 style='color: #4338ca;'>📓 Agenda de Clientes y Recuperación de Ventas</h2>", unsafe_allow_html=True)
    st.write("Registra clientes con tallas agotadas y gestiona el seguimiento por sucursal cuando el calzado ingrese a bodega.")

    # 1. Conectar a la pestaña de Google Sheets
    try:
        archivo = client_gs.open_by_key('1lGlVEBgu9QsrH9PYTTuoRKQeWnYiR7OwUElCsfkDgoM')
        sheet_agenda = archivo.worksheet('Agenda_Clientes')
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets (Asegúrate de haber creado la pestaña 'Agenda_Clientes'). Detalles: {e}")
        return

    # 2. Obtener lista REAL de sucursales desde tu Excel
    nombres_tiendas_reales = cargar_nombres_tiendas()
    lista_sucursales = ["Todas las Sucursales"] + nombres_tiendas_reales

    # Pestañas internas del módulo
    tab_alertas, tab_registro = st.tabs(["🚨 Panel de Alertas y Seguimiento", "📝 Nuevo Registro en Piso"])

    # ==========================================
    # TAB 1: PANEL DE ALERTAS Y SEGUIMIENTO (FILTRADO POR TIENDA)
    # ==========================================
    with tab_alertas:
        st.markdown("### 🔔 Clientes en Espera")

        # Filtro superior por Sucursal
        col_filtro1, col_filtro2 = st.columns([2, 1])
        with col_filtro1:
            sucursal_filtro = st.selectbox("🏪 Selecciona tu Sucursal:", lista_sucursales, key="filtro_sucursal_agenda")

        # Obtener datos de la nube
        datos = sheet_agenda.get_all_values()
        if len(datos) > 1:
            df_agenda = pd.DataFrame(datos[1:], columns=datos[0])
            
            # Filtrar solo pendientes (Estatus != CONTACTADO)
            df_pendientes = df_agenda[df_agenda['Estatus'].astype(str).str.upper() != 'CONTACTADO'].copy()
            
            # Aplicar filtro por la sucursal seleccionada
            if sucursal_filtro != "Todas las Sucursales":
                # Usamos exact match o contains para coincidir con la base
                df_pendientes = df_pendientes[df_pendientes['Sucursal'].astype(str).str.contains(sucursal_filtro, case=False, regex=False, na=False)]

            if df_pendientes.empty:
                st.success(f"✨ ¡Excelente! No hay clientes pendientes en lista de espera para {sucursal_filtro}.")
            else:
                st.caption(f"Mostrando **{len(df_pendientes)}** cliente(s) en espera para **{sucursal_filtro}**.")
                
                # Generar tarjetas por cada cliente
                for idx, row in df_pendientes.iterrows():
                    cliente = row.get('Cliente', 'Sin Nombre')
                    whatsapp = row.get('WhatsApp', '')
                    modelo = row.get('Modelo', '').upper()
                    talla = row.get('Talla', '')
                    sucursal = row.get('Sucursal', '')
                    fecha = row.get('Fecha', '')
                    notas = row.get('Notas', '')

                    # Mensaje personalizado de WhatsApp
                    mensaje = f"Hola {cliente}, te saludamos de Flexi {sucursal}. Te informamos que el modelo {modelo} en talla {talla} que buscabas ya está disponible. ¿Te lo apartamos?"
                    mensaje_url = urllib.parse.quote(mensaje)
                    link_wa = f"https://wa.me/52{whatsapp}?text={mensaje_url}" if whatsapp else "#"

                    # Diseño de la tarjeta
                    st.markdown(f"""
                    <div style="background-color: #1e293b; padding: 18px; border-radius: 10px; border-left: 5px solid #E30613; margin-bottom: 15px;">
                        <h4 style="color: white; margin-top: 0; margin-bottom: 5px;">👤 {cliente} - <span style="color: #fbbf24;">{sucursal}</span></h4>
                        <p style="color: #cbd5e1; margin: 3px 0; font-size: 14px;"><strong>Modelo:</strong> {modelo} | <strong>Talla:</strong> {talla} | <strong>Fecha:</strong> {fecha}</p>
                        {"<p style='color: #94a3b8; margin: 3px 0; font-size: 13px;'><em>Notas: " + notas + "</em></p>" if notas else ""}
                        <a href="{link_wa}" target="_blank" style="text-decoration: none;">
                            <button style="background-color: #25D366; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; margin-top: 10px;">
                                💬 Contactar vía WhatsApp
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
                # Usamos la lista de nombres_tiendas_reales directamente
                sucursal_input = st.selectbox("🏢 Selecciona tu Sucursal:", nombres_tiendas_reales)
                cliente_input = st.text_input("👤 Nombre del Cliente:")
                whatsapp_input = st.text_input("📱 WhatsApp (10 dígitos):", max_chars=10)
            
            with col2:
                modelo_input = st.text_input("👟 Modelo Buscado:")
                talla_input = st.number_input("📏 Talla (Ej. 25.0):", min_value=10.0, max_value=35.0, step=0.5, value=25.0)
                notas_input = st.text_area("📝 Notas (Opcional):", height=68)
            
            btn_guardar = st.form_submit_button("💾 Guardar Cliente", type="primary")
            
            if btn_guardar:
                if not cliente_input or not modelo_input:
                    st.error("⚠️ Faltan datos obligatorios (Cliente y Modelo).")
                elif len(whatsapp_input) < 10 or not whatsapp_input.isdigit():
                    st.error("⚠️ El número de WhatsApp debe tener 10 dígitos numéricos.")
                else:
                    # Guardar con fecha actual de México
                    fecha_hoy = (datetime.datetime.utcnow() - datetime.timedelta(hours=6)).strftime("%d/%m/%Y")
                    fila_nueva = [
                        fecha_hoy, sucursal_input, cliente_input, whatsapp_input, 
                        modelo_input.upper(), str(talla_input), notas_input, "ESPERANDO"
                    ]
                    
                    try:
                        sheet_agenda.append_row(fila_nueva)
                        st.success(f"✅ ¡Cliente {cliente_input} registrado exitosamente en {sucursal_input}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al guardar en la nube: {e}")
