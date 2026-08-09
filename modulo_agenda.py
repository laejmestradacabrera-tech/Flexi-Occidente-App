import streamlit as st
import pandas as pd
import datetime
import urllib.parse
import os
import re

def cargar_nombres_tiendas():
    """Función que lee automáticamente el archivo de tiendas real del monitor"""
    archivos = [f for f in os.listdir('.') if 'CORREO DE TIENDAS' in f.upper() and f.endswith(('.xlsx', '.csv'))]
    if archivos:
        archivo = sorted(archivos)[-1]
        try:
            df = pd.read_excel(archivo) if archivo.endswith('.xlsx') else pd.read_csv(archivo)
            df.columns = df.columns.astype(str).str.strip().str.upper()
            col_nom = 'NOMBRE' if 'NOMBRE' in df.columns else df.columns[1]
            nombres = df[col_nom].dropna().astype(str).unique().tolist()
            return sorted([n for n in nombres if n.strip() != ''])
        except Exception:
            pass
    return ["Sin Sucursales Cargadas"]

def clean_talla(t):
    """Normaliza tallas a string evitando que 25.5 se trunque o 25.0 no coincida con 25"""
    try:
        f = float(t)
        return str(int(f)) if f.is_integer() else str(f)
    except:
        return str(t).strip()

def asegurar_inventario_cargado():
    """Puente de memoria: Asegura que la agenda pueda leer el inventario local"""
    try:
        if 'df_ventas' not in st.session_state:
            archivos_v = [f for f in os.listdir('.') if 'Ventas' in f and f.endswith(('.xlsx', '.csv'))]
            if archivos_v:
                arch = sorted(archivos_v)[-1]
                st.session_state.df_ventas = pd.read_excel(arch) if arch.endswith('.xlsx') else pd.read_csv(arch)
                
        if 'df_tallas' not in st.session_state:
            archivos_t = [f for f in os.listdir('.') if 'Valores de tallas' in f and f.endswith(('.xlsx', '.csv'))]
            if archivos_t:
                arch = sorted(archivos_t)[-1]
                if arch.endswith('.xlsx'):
                    try: st.session_state.df_tallas = pd.read_excel(arch, sheet_name="Hoja1")
                    except: st.session_state.df_tallas = pd.read_excel(arch)
                else:
                    st.session_state.df_tallas = pd.read_csv(arch)
    except Exception:
        pass

def verificar_inventario_local(tda_int, modelo, talla):
    """Cruce silencioso con el Kárdex para saber si el zapato ya llegó a bodega"""
    try:
        if 'df_ventas' not in st.session_state or 'df_tallas' not in st.session_state:
            return False
            
        df_v = st.session_state.df_ventas
        df_t = st.session_state.df_tallas
        
        # Limpiar modelo y talla para cruce exacto
        mod_cln = str(modelo).replace(' ', '').replace('-', '').upper()
        t_buscada = clean_talla(talla)
        
        # Preparar base de ventas para filtro rápido
        if 'tienda_int_chk' not in df_v.columns:
            df_v['tienda_int_chk'] = pd.to_numeric(df_v['Tienda'].astype(str).str.extract(r'(\d+)', expand=False), errors='coerce').fillna(-1).astype(int)
            
        df_filtro = df_v[(df_v['tienda_int_chk'] == tda_int) & (df_v['Modelo'].astype(str).str.replace(' ', '').str.replace('-', '').str.upper() == mod_cln)]
        
        if df_filtro.empty: return False
        
        for idx, row in df_filtro.iterrows():
            dpto = str(row.get('Departamento', '')).strip().lower()
            tallas_row = df_t[df_t.iloc[:,0].astype(str).str.strip().str.lower() == dpto]
            
            if not tallas_row.empty:
                for i in range(1, 16):
                    col_ex = f'ex{i}'
                    if col_ex in tallas_row.columns:
                        val_matriz = tallas_row.iloc[0].get(col_ex, '')
                        if pd.notna(val_matriz) and str(val_matriz).strip() != '':
                            v_mat_str = clean_talla(val_matriz)
                            
                            if v_mat_str == t_buscada:
                                # ¡Talla encontrada en matriz! Checar si hay existencia > 0
                                existencia = row.get(col_ex, 0)
                                try: e_num = float(existencia)
                                except: e_num = 0.0
                                if e_num > 0: return True
        return False
    except:
        return False

# Inicializamos estados para la limpieza de la pantalla de registro
if 'agenda_reg_refresh' not in st.session_state:
    st.session_state.agenda_reg_refresh = False

def mostrar_modulo_agenda(client_gs):
    # Aseguramos cargar los archivos a la memoria (Darle "ojos" al módulo)
    asegurar_inventario_cargado()

    # Si se solicitó un refresh, limpiamos el estado y forzamos reinicio visual
    if st.session_state.get('agenda_reg_refresh', False):
        st.session_state.agenda_reg_refresh = False
        # No usamos rerun aquí, permitimos que el script fluya, los widgets tomarán sus defaults

    st.markdown("<h2 style='color: #4338ca;'>📓 Agenda de Clientes y Recuperación de Ventas</h2>", unsafe_allow_html=True)
    st.write("Registra clientes en piso de venta, cruza faltantes de talla con el inventario y gestiona tu cartera de clientes.")

    # 1. Conectar a Google Sheets
    try:
        archivo = client_gs.open_by_key('1lGlVEBgu9QsrH9PYTTuoRKQeWnYiR7OwUElCsfkDgoM')
        sheet_agenda = archivo.worksheet('Agenda_Clientes')
        datos = sheet_agenda.get_all_values()
        
        # Mantenimiento automático de la base de datos (Agrega columna Motivo si no existe)
        if len(datos) > 0 and 'Motivo' not in datos[0]:
            sheet_agenda.update_cell(1, len(datos[0]) + 1, 'Motivo')
            datos[0].append('Motivo')
            
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets (Asegúrate de tener la pestaña 'Agenda_Clientes'). Detalles: {e}")
        return

    nombres_tiendas_reales = cargar_nombres_tiendas()
    
    opcion_default = "👉 Selecciona tu sucursal..."
    opcion_gerencia = "Todas las Sucursales (Solo Gerencia)"
    lista_sucursales = [opcion_default, opcion_gerencia] + nombres_tiendas_reales

    tab_alertas, tab_registro = st.tabs(["🚨 Panel de Alertas y Seguimiento", "📝 Nuevo Registro en Piso"])

    # ==========================================
    # TAB 1: PANEL DE ALERTAS Y SEGUIMIENTO
    # ==========================================
    with tab_alertas:
        st.markdown("### 🔔 Trámites Activos")

        if 'ultimo_filtro_agenda' not in st.session_state:
            st.session_state.ultimo_filtro_agenda = opcion_default

        sucursal_filtro = st.selectbox("🏪 Selecciona tu Sucursal:", lista_sucursales, key="filtro_sucursal_agenda")

        if sucursal_filtro != st.session_state.ultimo_filtro_agenda:
            st.session_state.ultimo_filtro_agenda = sucursal_filtro
            if "clave_gerencia_agenda" in st.session_state:
                st.session_state.clave_gerencia_agenda = ""
            st.rerun()

        if sucursal_filtro == opcion_default:
            st.info("👆 Por favor, selecciona tu sucursal en el menú superior para cargar tu agenda.")
        else:
            # --- BOTÓN DE LIMPIEZA VISUAL (RESET) ---
            if st.button("🧹 Limpiar Pantalla / Cerrar Vista", use_container_width=True, type="secondary"):
                st.session_state.ultimo_filtro_agenda = opcion_default
                if "filtro_sucursal_agenda" in st.session_state:
                    del st.session_state["filtro_sucursal_agenda"]
                if "clave_gerencia_agenda" in st.session_state:
                    st.session_state.clave_gerencia_agenda = ""
                st.rerun()
                
            st.write("<br>", unsafe_allow_html=True)
            
            mostrar_tablero = True
            
            # Blindaje de Seguridad usando st.secrets
            if sucursal_filtro == opcion_gerencia:
                col_clave, _ = st.columns([1, 2])
                with col_clave:
                    clave_ingresada = st.text_input("🔐 Clave de Autorización:", type="password", key="clave_gerencia_agenda")
                
                clave_maestra = "Flexi2026"
                try: clave_maestra = st.secrets.get("CLAVE_GERENCIA", "Flexi2026")
                except: pass
                
                if clave_ingresada != clave_maestra:
                    st.warning("🔒 Vista restringida. Ingresa la clave corporativa para acceder al tablero global.")
                    mostrar_tablero = False
            
            if mostrar_tablero:
                if len(datos) > 1:
                    df_agenda = pd.DataFrame(datos[1:], columns=datos[0])
                    
                    # Rellenar motivos vacíos con 'Falta de Talla' para respetar registros históricos
                    if 'Motivo' in df_agenda.columns:
                        df_agenda['Motivo'] = df_agenda['Motivo'].replace('', '📦 Falta de Talla').fillna('📦 Falta de Talla')
                    else:
                        df_agenda['Motivo'] = '📦 Falta de Talla'
                    
                    # Filtro maestro de pendientes
                    df_pendientes = df_agenda[df_agenda['Estatus'].astype(str).str.upper() != 'CONTACTADO'].copy()
                    
                    if sucursal_filtro != opcion_gerencia:
                        df_pendientes = df_pendientes[df_pendientes['Sucursal'].astype(str).str.contains(sucursal_filtro, case=False, regex=False, na=False)]

                    # --- SECCIÓN A: ALERTAS DE QUIEBRE (MOTOR INTELIGENTE) ---
                    df_faltas = df_pendientes[df_pendientes['Motivo'].astype(str).str.contains('Falta', case=False, na=False)]
                    
                    if df_faltas.empty:
                        st.success(f"✨ No tienes registros de 'Falta de Talla' pendientes para {sucursal_filtro}.")
                    else:
                        st.caption(f"Mostrando **{len(df_faltas)}** registros de calzado en espera.")
                        
                        pendientes_list = list(df_faltas.iterrows())
                        
                        # Carga de tiendas para traducir nombre a ID para la alerta
                        df_tiendas_alertas = pd.DataFrame()
                        arch_tiendas = [f for f in os.listdir('.') if 'CORREO DE TIENDAS' in f.upper() and f.endswith(('.xlsx', '.csv'))]
                        if arch_tiendas:
                            try:
                                arch = sorted(arch_tiendas)[-1]
                                df_tiendas_alertas = pd.read_excel(arch) if arch.endswith('.xlsx') else pd.read_csv(arch)
                                df_tiendas_alertas.columns = df_tiendas_alertas.columns.astype(str).str.strip().str.upper()
                            except: pass

                        for i in range(0, len(pendientes_list), 2):
                            cols = st.columns(2)
                            
                            for j in range(2):
                                if i + j < len(pendientes_list):
                                    idx, row = pendientes_list[i + j]
                                    with cols[j]:
                                        cliente = row.get('Cliente', 'Sin Nombre')
                                        whatsapp = row.get('Whatsapp', row.get('WhatsApp', '')) 
                                        modelo = row.get('Modelo', '').upper()
                                        talla = row.get('Talla', '')
                                        sucursal = row.get('Sucursal', '')
                                        notas = row.get('Notas', '')

                                        # Obtener ID de la tienda desde el archivo maestro para la alerta
                                        tda_num_alerta = -1
                                        if not df_tiendas_alertas.empty:
                                            col_nom_alerta = 'NOMBRE' if 'NOMBRE' in df_tiendas_alertas.columns else (df_tiendas_alertas.columns[1] if len(df_tiendas_alertas.columns) > 1 else df_tiendas_alertas.columns[0])
                                            fila_alerta = df_tiendas_alertas[df_tiendas_alertas[col_nom_alerta].astype(str).str.strip().str.upper() == str(sucursal).strip().upper()]
                                            
                                            if not fila_alerta.empty:
                                                for col in df_tiendas_alertas.columns:
                                                    if col.strip().upper() in ['TIENDA', 'SUCURSAL', 'NUMERO', 'ID']:
                                                        try:
                                                            match_num = re.search(r'\d+', str(fila_alerta[col].values[0]))
                                                            if match_num: tda_num_alerta = int(match_num.group())
                                                        except: pass
                                                        break

                                        # Cruce con inventario local usando el ID exacto
                                        zapato_llegado = verificar_inventario_local(tda_num_alerta, modelo, talla)

                                        # Renderizado dinámico de la tarjeta (Semáforo)
                                        if zapato_llegado:
                                            html_tarjeta = f"""
                                            <div style="padding: 15px; border: 2px solid #22c55e; background-color: #1e293b; border-radius: 8px 8px 0 0; box-shadow: 0 0 15px rgba(34,197,94,0.3);">
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                                    <span style="color: #22c55e; font-weight: 900; font-size: 13px; letter-spacing: 1px;">🟢 ¡CALZADO EN BODEGA!</span>
                                                    <span style="color: #94a3b8; font-size: 11px;">Falta de Talla</span>
                                                </div>
                                                <p style="margin: 0; font-size: 14.5px; color: #f8fafc; line-height: 1.4;">
                                                    Llamar al cliente <strong>{cliente}</strong> al <strong style="color: #fbbf24;">{whatsapp}</strong>.<br>El modelo <strong>{modelo}</strong> (Talla {talla}) ya está físicamente en tienda.
                                                </p>
                                                {"<p style='margin: 8px 0 0 0; font-size: 12px; color: #94a3b8;'><em>📝 Notas: " + notas + "</em></p>" if notas else ""}
                                            </div>
                                            """
                                        else:
                                            html_tarjeta = f"""
                                            <div style="padding: 15px; border: 1px solid #334155; background-color: #0f172a; border-radius: 8px 8px 0 0;">
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                                    <span style="color: #64748b; font-weight: 700; font-size: 12px;">⏳ Esperando llegada...</span>
                                                    <span style="color: #475569; font-size: 11px;">Falta de Talla</span>
                                                </div>
                                                <p style="margin: 0; font-size: 14.5px; color: #cbd5e1; line-height: 1.4;">
                                                    <strong>{cliente}</strong> ({whatsapp})<br>Buscando modelo <strong>{modelo}</strong> (Talla {talla}).
                                                </p>
                                                {"<p style='margin: 8px 0 0 0; font-size: 12px; color: #64748b;'><em>📝 Notas: " + notas + "</em></p>" if notas else ""}
                                            </div>
                                            """
                                            
                                        st.markdown(html_tarjeta, unsafe_allow_html=True)
                                        
                                        # Botón para limpiar registro
                                        btn_type = "primary" if zapato_llegado else "secondary"
                                        if st.button("✅ Marcar como Contactado", key=f"btn_done_{idx}", use_container_width=True, type=btn_type):
                                            try:
                                                sheet_agenda.update_cell(idx + 2, 8, "CONTACTADO")
                                                st.toast(f"¡Excelente! Cliente {cliente} contactado.", icon="✅")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error al actualizar: {e}")
                                        
                                        st.write("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

                    st.markdown("---")
                    
                    # --- SECCIÓN B: AGENDA COMPLETA (DIRECTORIO PASIVO) ---
                    with st.expander("📓 Abrir Agenda / Directorio General de Tienda", expanded=False):
                        st.markdown("<p style='color:#64748b; font-size:13px;'>Esta sección muestra todo tu padrón de clientes pendientes (Faltantes y Avisos de Promoción) para consulta telefónica pasiva. Los registros no se borran desde aquí.</p>", unsafe_allow_html=True)
                        
                        if df_pendientes.empty:
                            st.info("Tu directorio de clientes está vacío.")
                        else:
                            df_mostrar = pd.DataFrame()
                            df_mostrar['CLIENTE'] = df_pendientes['Cliente']
                            df_mostrar['TELÉFONO'] = df_pendientes['Whatsapp']
                            df_mostrar['MOTIVO DEL REGISTRO'] = df_pendientes['Motivo']
                            
                            def format_modelo_talla(row):
                                mod = str(row.get('Modelo', '')).strip()
                                tal = str(row.get('Talla', '')).strip()
                                if mod and mod.upper() != 'NAN':
                                    if tal and tal.upper() != 'NAN' and tal != '':
                                        return f"Mod. {mod} (T. {tal})"
                                    return f"Mod. {mod}"
                                return ""
                                
                            df_mostrar['MODELO Y TALLA'] = df_pendientes.apply(format_modelo_talla, axis=1)
                            df_mostrar['NOTAS ADICIONALES'] = df_pendientes['Notas']
                            
                            st.table(df_mostrar)
                else:
                    st.info("Aún no hay registros en la base de datos.")

    # ==========================================
    # TAB 2: FORMULARIO DE REGISTRO DUAL (CLON DE BITÁCORA)
    # ==========================================
    with tab_registro:
        st.markdown("### 📝 Captura de Datos en Caja")

        # 1. Extractor Robusto de Tiendas (Idéntico a Bitácora)
        df_tdas_reg = pd.DataFrame()
        archivos_t = [f for f in os.listdir('.') if 'CORREO DE TIENDAS' in f.upper() and f.endswith(('.xlsx', '.csv'))]
        if archivos_t:
            try:
                arch = sorted(archivos_t)[-1]
                df_tdas_reg = pd.read_excel(arch) if arch.endswith('.xlsx') else pd.read_csv(arch)
                df_tdas_reg.columns = df_tdas_reg.columns.astype(str).str.strip().str.upper()
            except: pass

        if df_tdas_reg.empty:
            st.warning("No se pudo cargar el archivo de sucursales.")
            nombres_sucursales = ["Sin Sucursales"]
        else:
            col_nom_reg = 'NOMBRE' if 'NOMBRE' in df_tdas_reg.columns else (df_tdas_reg.columns[1] if len(df_tdas_reg.columns) > 1 else df_tdas_reg.columns[0])
            nombres_sucursales = sorted(df_tdas_reg[col_nom_reg].dropna().astype(str).unique().tolist())
            nombres_sucursales = [n for n in nombres_sucursales if n.strip() != '']

        col1, col2 = st.columns([2, 1])
        
        with col1:
            sucursal_input = st.selectbox("Selecciona la Tienda:", nombres_sucursales, key="agenda_reg_sucursal")
            
        # Extracción del Número de Tienda (ID)
        tda_num_defecto = ""
        if not df_tdas_reg.empty:
            fila_tienda = df_tdas_reg[df_tdas_reg[col_nom_reg] == sucursal_input]
            if not fila_tienda.empty:
                for col in df_tdas_reg.columns:
                    if col.strip().upper() in ['TIENDA', 'SUCURSAL', 'NUMERO', 'ID']:
                        tda_num_defecto = str(fila_tienda[col].values[0])
                        break
        
        with col2:
            st.markdown("**N° Sucursal en SAP/Inventario:**")
            st.info(f"🏪 {tda_num_defecto if tda_num_defecto else 'No encontrado'}")

        motivo_input = st.selectbox("📌 Motivo del Registro:", ["📦 Falta de Talla (Quiebre)", "🏷️ Agenda (Aviso de Promociones)"], key="agenda_reg_motivo")
        
        cliente_input = st.text_input("👤 Nombre del Cliente:", key="agenda_reg_cliente")
        whatsapp_input = st.text_input("📱 Teléfono (10 dígitos):", max_chars=10, key="agenda_reg_telefono")
        
        modelo_input = ""
        talla_input = 0.0
        
        # Condicional simple, igual que en la Bitácora
        if "Falta" in motivo_input:
            col_mod, col_tal = st.columns(2)
            with col_mod:
                modelo_input = st.text_input("👟 Modelo Buscado:", key="agenda_reg_modelo")
            with col_tal:
                talla_input = st.number_input("📏 Talla (Ej. 250 o 25.0):", min_value=1.0, max_value=350.0, step=0.5, value=25.0, key="agenda_reg_talla")
        else:
            st.info("💡 En modo Agenda (Promociones) no se requiere capturar Modelo ni Talla.")
            
        notas_input = st.text_area("📝 Notas (Opcional):", key="agenda_reg_notas")

        st.write("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            btn_guardar = st.button("💾 Guardar Cliente", type="primary", use_container_width=True)
            
        with col_btn2:
            if st.button("🧹 Limpiar Formulario", type="secondary", use_container_width=True):
                st.session_state.agenda_reg_refresh = True
                st.rerun()

        if btn_guardar:
            puede_guardar = True
            
            if not cliente_input:
                st.error("⚠️ El nombre del cliente es obligatorio.")
                puede_guardar = False
            elif len(whatsapp_input) < 10 or not whatsapp_input.isdigit():
                st.error("⚠️ El número de Teléfono debe tener 10 dígitos numéricos.")
                puede_guardar = False
                
            if "Falta" in motivo_input and puede_guardar:
                if not modelo_input:
                    st.error("⚠️ Para reportar falta de tallas, debes escribir el Modelo.")
                    puede_guardar = False
                elif not tda_num_defecto.strip().isdigit():
                    st.error("❌ No se detectó un N° de Sucursal válido. El sistema no puede cruzar el inventario.")
                    puede_guardar = False
                else:
                    # --- ESCUDO DE INVENTARIO: Llamamos a la validación robusta local ---
                    tienda_id_int = int(tda_num_defecto.strip())
                    if verificar_inventario_local(tienda_id_int, modelo_input, talla_input):
                        st.error(f"⛔ ¡ALTO! El modelo {modelo_input.upper()} (Talla {talla_input}) SÍ tiene existencia física en la sucursal {tienda_id_int}. Ve a bodega y entrégalo al cliente.")
                        puede_guardar = False

            if puede_guardar:
                fecha_hoy = (datetime.datetime.utcnow() - datetime.timedelta(hours=6)).strftime("%d/%m/%Y")
                
                # Estructura alineada a 9 columnas
                fila_nueva = [
                    fecha_hoy, sucursal_input, cliente_input, whatsapp_input, 
                    modelo_input.upper(), str(talla_input), notas_input, "ESPERANDO", motivo_input
                ]
                
                try:
                    sheet_agenda.append_row(fila_nueva)
                    st.success(f"✅ ¡Cliente {cliente_input} registrado exitosamente bajo el motivo: {motivo_input.split(' ')[1]}!")
                    
                    # Activamos el refresh para que la pantalla se limpie tras mostrar el mensaje de éxito (al próximo clic)
                    st.info("💡 Formulario guardado. Presiona 'Limpiar Formulario' o cambia de pestaña para continuar.")
                except Exception as e:
                    st.error(f"❌ Error al guardar en la nube: {e}")
