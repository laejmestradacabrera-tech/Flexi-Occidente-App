import streamlit as st
import pandas as pd
import datetime
import urllib.parse
import os
import re
import time

# --- CACHÉ MAESTRO PARA EVITAR LAG Y RESETEOS EN EL MENÚ ---
@st.cache_data
def obtener_catalogo_tiendas():
    """Carga el catálogo de tiendas una sola vez en memoria para estabilizar los selectbox"""
    archivos = [f for f in os.listdir('.') if 'CORREO DE TIENDAS' in f.upper() and f.endswith(('.xlsx', '.csv'))]
    if archivos:
        archivo = sorted(archivos)[-1]
        try:
            df = pd.read_excel(archivo) if archivo.endswith('.xlsx') else pd.read_csv(archivo)
            df.columns = df.columns.astype(str).str.strip().str.upper()
            return df
        except Exception:
            pass
    return pd.DataFrame()

def clean_talla(t):
    """
    Normaliza la talla al formato que utiliza Ventas.xlsx / Valores de tallas.xlsx.

    El inventario trabaja con tallas en décimas de centímetro:
        220, 225, 230, 235...

    La tienda puede capturar la talla en formato comercial:
        22, 22.5, 23, 23.5...

    Por eso ambos formatos se convierten al mismo valor canónico:
        22   -> 220
        22.5 -> 225
        25   -> 250
        25.5 -> 255
        250  -> 250
        255  -> 255
    """
    try:
        if t is None or (isinstance(t, float) and pd.isna(t)):
            return ""

        texto = str(t).strip().replace(',', '.')
        if not texto:
            return ""

        f = float(texto)

        # Formato comercial (22, 22.5, 25, 25.5, etc.)
        # se convierte al formato del archivo de inventario (220, 225, 250, 255...).
        if 1 <= f < 100:
            f = round(f * 10)

        # El inventario trabaja con valores enteros.
        return str(int(round(f)))
    except (TypeError, ValueError):
        return str(t).strip()

def asegurar_inventario_cargado():
    """Carga una sola vez los archivos maestros de inventario y tallas."""
    try:
        if 'df_ventas' not in st.session_state:
            archivos_v = [
                f for f in os.listdir('.')
                if f.lower().startswith('ventas') and f.lower().endswith(('.xlsx', '.csv'))
            ]
            if archivos_v:
                # Preferimos el archivo Ventas.xlsx; si existe más de uno,
                # tomamos el más reciente por nombre ordenado como respaldo.
                arch = next((f for f in archivos_v if f.lower() == 'ventas.xlsx'), sorted(archivos_v)[-1])
                st.session_state.df_ventas = (
                    pd.read_excel(arch) if arch.lower().endswith('.xlsx') else pd.read_csv(arch)
                )

        if 'df_tallas' not in st.session_state:
            archivos_t = [
                f for f in os.listdir('.')
                if f.lower().startswith('valores de tallas') and f.lower().endswith(('.xlsx', '.csv'))
            ]
            if archivos_t:
                arch = next((f for f in archivos_t if f.lower() == 'valores de tallas.xlsx'), sorted(archivos_t)[-1])
                if arch.lower().endswith('.xlsx'):
                    try:
                        st.session_state.df_tallas = pd.read_excel(arch, sheet_name='Hoja1')
                    except Exception:
                        st.session_state.df_tallas = pd.read_excel(arch)
                else:
                    st.session_state.df_tallas = pd.read_csv(arch)
    except Exception as e:
        st.session_state.inventario_carga_error = str(e)

def validar_inventario_local(tda_int, modelo, talla):
    """
    Valida inventario y devuelve un estado explícito:
        EXISTE     -> hay existencia física de la talla solicitada.
        NO_EXISTE  -> el modelo/talla no tiene existencia.
        ERROR      -> no fue posible validar; nunca debe interpretarse como quiebre.
    """
    try:
        if 'df_ventas' not in st.session_state or 'df_tallas' not in st.session_state:
            return 'ERROR'

        df_v = st.session_state.df_ventas.copy()
        df_t = st.session_state.df_tallas.copy()

        df_v.columns = df_v.columns.astype(str).str.strip().str.lower()
        df_t.columns = df_t.columns.astype(str).str.strip().str.lower()

        mod_cln = str(modelo).replace(' ', '').replace('-', '').upper()
        t_buscada = clean_talla(talla)

        if not t_buscada:
            return 'ERROR'

        columnas_obligatorias = {'tienda', 'modelo', 'departamento'}
        if not columnas_obligatorias.issubset(set(df_v.columns)):
            return 'ERROR'

        if 'valor' not in df_t.columns:
            return 'ERROR'

        # Convertimos el número de tienda a entero de forma robusta.
        tienda_series = pd.to_numeric(
            df_v['tienda'].astype(str).str.extract(r'(\d+)', expand=False),
            errors='coerce'
        )
        df_v['tienda_int_chk'] = tienda_series.fillna(-1).astype(int)

        # Normalizamos modelo para evitar diferencias por espacios/guiones.
        modelos_norm = (
            df_v['modelo'].astype(str)
            .str.replace(' ', '', regex=False)
            .str.replace('-', '', regex=False)
            .str.upper()
        )

        df_filtro = df_v[
            (df_v['tienda_int_chk'] == int(tda_int)) &
            (modelos_norm == mod_cln)
        ]

        # Si no hay el modelo en esa tienda, es un quiebre real de modelo.
        if df_filtro.empty:
            return 'NO_EXISTE'

        # Buscamos la matriz correspondiente al departamento.
        for _, row in df_filtro.iterrows():
            dpto = str(row.get('departamento', '')).strip().lower()
            tallas_row = df_t[
                df_t['valor'].astype(str).str.strip().str.lower() == dpto
            ]

            if tallas_row.empty:
                # El modelo existe, pero no conocemos cómo mapear sus tallas.
                return 'ERROR'

            for i in range(1, 16):
                col_ex = f'ex{i}'

                if col_ex not in tallas_row.columns or col_ex not in row.index:
                    continue

                val_matriz = tallas_row.iloc[0].get(col_ex, '')

                if pd.isna(val_matriz) or str(val_matriz).strip() == '':
                    continue

                if clean_talla(val_matriz) != t_buscada:
                    continue

                # Talla encontrada: ahora sí revisamos existencia física.
                existencia = row.get(col_ex, 0)
                try:
                    e_num = float(existencia)
                except (TypeError, ValueError):
                    return 'ERROR'

                return 'EXISTE' if e_num > 0 else 'NO_EXISTE'

        # El modelo existe, pero la talla no está contemplada en su matriz.
        return 'NO_EXISTE'

    except Exception as e:
        st.session_state.ultimo_error_inventario = str(e)
        return 'ERROR'


def verificar_inventario_local(tda_int, modelo, talla):
    """Compatibilidad con el resto del módulo: True solo cuando hay existencia."""
    return validar_inventario_local(tda_int, modelo, talla) == 'EXISTE'

# --- CALLBACK DE LIMPIEZA ---
# Esta función nativa se ejecuta ANTES de refrescar la pantalla, previniendo el StreamlitAPIException
def limpiar_formulario_agenda():
    claves = ["agenda_reg_sucursal", "agenda_reg_motivo", "agenda_reg_cliente", "agenda_reg_telefono", "agenda_reg_modelo", "agenda_reg_talla", "agenda_reg_notas"]
    for key in claves:
        if key in st.session_state:
            del st.session_state[key]

# Inicializamos estados para la limpieza de la pantalla de registro
if 'agenda_reg_refresh' not in st.session_state:
    st.session_state.agenda_reg_refresh = False

# --- CACHE DE AGENDA GOOGLE SHEETS ---
# Evita leer toda la hoja en cada rerun de Streamlit.
# La agenda se lee una vez y se conserva temporalmente en la sesión.
AGENDA_CACHE_TTL = 20  # segundos

def obtener_sheet_agenda(client_gs):
    """Obtiene y conserva el objeto de Google Sheets durante la sesión."""
    try:
        if 'sheet_agenda_obj' not in st.session_state:
            archivo = client_gs.open_by_key('1lGlVEBgu9QsrH9PYTTuoRKQeWnYiR7OwUElCsfkDgoM')
            st.session_state.sheet_agenda_obj = archivo.worksheet('Agenda_Clientes')
        return st.session_state.sheet_agenda_obj
    except Exception as e:
        st.session_state.sheet_agenda_error = str(e)
        return None

def leer_agenda_google(sheet_agenda, forzar=False):
    """Lee Agenda_Clientes solo cuando es necesario y conserva una copia local."""
    ahora = time.time()
    datos_cache = st.session_state.get('agenda_datos_cache')
    ultima_lectura = st.session_state.get('agenda_cache_timestamp', 0)

    # Usamos la copia local durante el TTL. Esto evita get_all_values() en cada rerun.
    if not forzar and datos_cache is not None and (ahora - ultima_lectura) < AGENDA_CACHE_TTL:
        return datos_cache, None

    try:
        datos = sheet_agenda.get_all_values()

        # Mantenimiento automático de la base de datos. Solo se ejecuta si realmente falta Motivo.
        if len(datos) > 0:
            encabezados = [str(c).strip() for c in datos[0]]
            if 'Motivo' not in encabezados:
                sheet_agenda.update_cell(1, len(datos[0]) + 1, 'Motivo')
                datos[0].append('Motivo')

            # Normalizamos el ancho de todas las filas para que el DataFrame
            # nunca falle si alguna fila histórica todavía no tiene Motivo.
            ancho = len(datos[0])
            for fila in datos[1:]:
                while len(fila) < ancho:
                    fila.append('📦 Falta de Talla' if len(fila) == ancho - 1 else '')
                if len(fila) > ancho:
                    del fila[ancho:]

        st.session_state.agenda_datos_cache = datos
        st.session_state.agenda_cache_timestamp = ahora
        st.session_state.agenda_cache_error = None
        return datos, None

    except Exception as e:
        mensaje = str(e)
        # Si Google devuelve 429 pero tenemos una copia previa, seguimos trabajando con ella.
        if datos_cache is not None:
            st.session_state.agenda_cache_error = mensaje
            return datos_cache, mensaje
        st.session_state.agenda_cache_error = mensaje
        return None, mensaje

def invalidar_cache_agenda():
    """Marca la copia local como actualizada sin obligar una nueva lectura."""
    st.session_state.agenda_cache_timestamp = time.time()

def mostrar_modulo_agenda(client_gs):
    # Aseguramos cargar los inventarios a la memoria
    asegurar_inventario_cargado()

    # Si se solicitó un refresh, limpiamos el estado y permitimos reinicio visual
    if st.session_state.get('agenda_reg_refresh', False):
        st.session_state.agenda_reg_refresh = False

    st.markdown("<h2 style='color: #4338ca;'>📓 Agenda de Clientes y Recuperación de Ventas</h2>", unsafe_allow_html=True)
    st.write("Registra clientes en piso de venta, cruza faltantes de talla con el inventario y gestiona tu cartera de clientes.")

    # 1. Cargar el Catálogo de Tiendas de forma global y estable
    df_tdas_global = obtener_catalogo_tiendas()
    nombres_sucursales = ["Sin Sucursales Cargadas"]
    col_nom_global = 'NOMBRE'
    
    if not df_tdas_global.empty:
        col_nom_global = 'NOMBRE' if 'NOMBRE' in df_tdas_global.columns else (df_tdas_global.columns[1] if len(df_tdas_global.columns) > 1 else df_tdas_global.columns[0])
        nombres_sucursales = sorted(df_tdas_global[col_nom_global].dropna().astype(str).unique().tolist())
        nombres_sucursales = [n for n in nombres_sucursales if n.strip() != '']

    # 2. Conectar a Google Sheets sin leer la hoja en cada rerun
    sheet_agenda = obtener_sheet_agenda(client_gs)
    if sheet_agenda is None:
        st.error(
            "❌ No fue posible abrir la pestaña 'Agenda_Clientes'. "
            f"Detalles: {st.session_state.get('sheet_agenda_error', 'Error desconocido')}"
        )
        return

    datos, error_lectura = leer_agenda_google(sheet_agenda)

    if datos is None:
        if '429' in str(error_lectura):
            st.error(
                "⏳ Google Sheets alcanzó temporalmente el límite de lecturas. "
                "No se realizó ninguna modificación. Espera unos segundos y vuelve a entrar al módulo."
            )
        else:
            st.error(
                "❌ Error al leer Google Sheets. "
                f"Detalles: {error_lectura}"
            )
        return

    if error_lectura and '429' in str(error_lectura):
        st.warning(
            "⚠️ Google Sheets está limitando temporalmente las lecturas. "
            "El sistema está trabajando con la última copia disponible y no volverá a leer la hoja en cada refresco."
        )

    opcion_default = "👉 Selecciona tu sucursal..."
    opcion_gerencia = "Todas las Sucursales (Solo Gerencia)"
    lista_sucursales_menu = [opcion_default, opcion_gerencia] + nombres_sucursales

    tab_alertas, tab_registro = st.tabs(["🚨 Panel de Alertas y Seguimiento", "📝 Nuevo Registro en Piso"])

    # ==========================================
    # TAB 1: PANEL DE ALERTAS Y SEGUIMIENTO
    # ==========================================
    with tab_alertas:
        st.markdown("### 🔔 Trámites Activos")

        col_refrescar, col_estado = st.columns([1, 2])
        with col_refrescar:
            if st.button("🔄 Actualizar Agenda", use_container_width=True, type="secondary"):
                datos_nuevos, error_nuevo = leer_agenda_google(sheet_agenda, forzar=True)
                if datos_nuevos is not None:
                    st.success("Agenda actualizada.")
                    st.rerun()
                elif '429' in str(error_nuevo):
                    st.warning("⏳ Google Sheets sigue limitando las lecturas. Espera unos segundos antes de volver a actualizar.")
                else:
                    st.error(f"No se pudo actualizar la agenda: {error_nuevo}")
        with col_estado:
            edad_cache = int(max(0, time.time() - st.session_state.get('agenda_cache_timestamp', time.time())))
            st.caption(f"📡 Última lectura de Google Sheets: hace {edad_cache} s · Cache local activo")

        if 'ultimo_filtro_agenda' not in st.session_state:
            st.session_state.ultimo_filtro_agenda = opcion_default

        sucursal_filtro = st.selectbox("🏪 Selecciona tu Sucursal:", lista_sucursales_menu, key="filtro_sucursal_agenda")

        if sucursal_filtro != st.session_state.ultimo_filtro_agenda:
            st.session_state.ultimo_filtro_agenda = sucursal_filtro
            if "clave_gerencia_agenda" in st.session_state:
                st.session_state.clave_gerencia_agenda = ""
            st.rerun()

        if sucursal_filtro == opcion_default:
            st.info("👆 Por favor, selecciona tu sucursal en el menú superior para cargar tu agenda.")
        else:
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
                
                # La clave debe existir en st.secrets; no dejamos una contraseña
                # corporativa expuesta como respaldo dentro del código.
                try:
                    clave_maestra = st.secrets["CLAVE_GERENCIA"]
                except Exception:
                    clave_maestra = None

                if not clave_maestra or clave_ingresada != clave_maestra:
                    st.warning("🔒 Vista restringida. Ingresa la clave corporativa para acceder al tablero global.")
                    mostrar_tablero = False
            
            if mostrar_tablero:
                if len(datos) > 1:
                    df_agenda = pd.DataFrame(datos[1:], columns=datos[0])
                    
                    if 'Motivo' in df_agenda.columns:
                        df_agenda['Motivo'] = df_agenda['Motivo'].replace('', '📦 Falta de Talla').fillna('📦 Falta de Talla')
                    else:
                        df_agenda['Motivo'] = '📦 Falta de Talla'
                    
                    df_pendientes = df_agenda[df_agenda['Estatus'].astype(str).str.upper() != 'CONTACTADO'].copy()
                    
                    if sucursal_filtro != opcion_gerencia:
                        df_pendientes = df_pendientes[df_pendientes['Sucursal'].astype(str).str.contains(sucursal_filtro, case=False, regex=False, na=False)]

                    df_faltas = df_pendientes[df_pendientes['Motivo'].astype(str).str.contains('Falta', case=False, na=False)]
                    
                    if df_faltas.empty:
                        st.success(f"✨ No tienes registros de 'Falta de Talla' pendientes para {sucursal_filtro}.")
                    else:
                        st.caption(f"Mostrando **{len(df_faltas)}** registros de calzado en espera.")
                        
                        pendientes_list = list(df_faltas.iterrows())

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

                                        tda_num_alerta = -1
                                        if not df_tdas_global.empty:
                                            fila_alerta = df_tdas_global[df_tdas_global[col_nom_global].astype(str).str.strip().str.upper() == str(sucursal).strip().upper()]
                                            if not fila_alerta.empty:
                                                for col in df_tdas_global.columns:
                                                    if col.strip().upper() in ['TIENDA', 'SUCURSAL', 'NUMERO', 'ID']:
                                                        try:
                                                            match_num = re.search(r'\d+', str(fila_alerta[col].values[0]))
                                                            if match_num: tda_num_alerta = int(match_num.group())
                                                        except: pass
                                                        break

                                        zapato_llegado = verificar_inventario_local(tda_num_alerta, modelo, talla)

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
                                        
                                        btn_type = "primary" if zapato_llegado else "secondary"
                                        if st.button("✅ Marcar como Contactado", key=f"btn_done_{idx}", use_container_width=True, type=btn_type):
                                            try:
                                                # No asumimos que Estatus está siempre en la columna 8.
                                                encabezados = [str(c).strip().lower() for c in datos[0]]
                                                if 'estatus' not in encabezados:
                                                    raise ValueError("La hoja Agenda_Clientes no contiene la columna 'Estatus'.")
                                                col_estatus = encabezados.index('estatus') + 1
                                                # Actualizamos una sola celda en Google Sheets.
                                                sheet_agenda.update_cell(idx + 2, col_estatus, "CONTACTADO")

                                                # Actualizamos también la copia local para que el rerun NO vuelva a hacer get_all_values().
                                                datos_local = [list(fila) for fila in st.session_state.get('agenda_datos_cache', datos)]
                                                fila_local = idx + 1  # datos incluye encabezado en la posición 0.
                                                col_local = col_estatus - 1
                                                if 0 <= fila_local < len(datos_local):
                                                    while len(datos_local[fila_local]) <= col_local:
                                                        datos_local[fila_local].append('')
                                                    datos_local[fila_local][col_local] = "CONTACTADO"
                                                    st.session_state.agenda_datos_cache = datos_local
                                                    invalidar_cache_agenda()

                                                st.toast(f"¡Excelente! Cliente {cliente} contactado.", icon="✅")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error al actualizar: {e}")
                                        
                                        st.write("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

                    st.markdown("---")
                    
                    with st.expander("📓 Abrir Agenda / Directorio General de Tienda", expanded=False):
                        st.markdown("<p style='color:#64748b; font-size:13px;'>Esta sección muestra <strong>todo tu padrón histórico de clientes</strong> (Faltantes y Avisos de Promoción), incluyendo los que ya fueron contactados. Los registros no se borran desde aquí.</p>", unsafe_allow_html=True)

                        # IMPORTANTE: el padrón es histórico y NO debe depender del Estatus.
                        # df_pendientes se utiliza únicamente para el panel de seguimiento.
                        # Aquí mostramos todos los registros de df_agenda, incluidos CONTACTADO.
                        df_directorio = df_agenda.copy()
                        if sucursal_filtro != opcion_gerencia:
                            df_directorio = df_directorio[
                                df_directorio['Sucursal'].astype(str).str.contains(
                                    sucursal_filtro, case=False, regex=False, na=False
                                )
                            ]

                        if df_directorio.empty:
                            st.info("Tu directorio de clientes está vacío.")
                        else:
                            df_mostrar = pd.DataFrame()
                            df_mostrar['CLIENTE'] = df_directorio['Cliente']
                            df_mostrar['TELÉFONO'] = df_directorio['Whatsapp']
                            df_mostrar['MOTIVO DEL REGISTRO'] = df_directorio['Motivo']
                            
                            def format_modelo_talla(row):
                                mod = str(row.get('Modelo', '')).strip()
                                tal = str(row.get('Talla', '')).strip()
                                if mod and mod.upper() != 'NAN':
                                    if tal and tal.upper() != 'NAN' and tal != '':
                                        return f"Mod. {mod} (T. {tal})"
                                    return f"Mod. {mod}"
                                return ""
                                
                            df_mostrar['MODELO Y TALLA'] = df_directorio.apply(format_modelo_talla, axis=1)
                            df_mostrar['NOTAS ADICIONALES'] = df_directorio['Notas']
                            
                            st.caption(f"Mostrando **{len(df_directorio)}** clientes registrados, incluyendo clientes ya contactados.")
                            st.table(df_mostrar)
                else:
                    st.info("Aún no hay registros en la base de datos.")

    # ==========================================
    # TAB 2: FORMULARIO DE REGISTRO DUAL
    # ==========================================
    with tab_registro:
        st.markdown("### 📝 Captura de Datos en Caja")

        col1, col2 = st.columns([2, 1])
        
        with col1:
            sucursal_input = st.selectbox("Selecciona la Tienda:", nombres_sucursales, key="agenda_reg_sucursal")
            
        tda_num_defecto = ""
        if not df_tdas_global.empty and sucursal_input != "Sin Sucursales Cargadas":
            fila_tienda = df_tdas_global[df_tdas_global[col_nom_global] == sucursal_input]
            if not fila_tienda.empty:
                for col in df_tdas_global.columns:
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
        
        if "Falta" in motivo_input:
            col_mod, col_tal = st.columns(2)
            with col_mod:
                modelo_input = st.text_input("👟 Modelo Buscado:", key="agenda_reg_modelo")
            with col_tal:
                talla_input = st.number_input("📏 Talla (Ej. 25, 25.5, 250 o 255):", min_value=1.0, max_value=350.0, step=0.5, value=25.0, key="agenda_reg_talla")
        else:
            st.info("💡 En modo Agenda (Promociones) no se requiere capturar Modelo ni Talla.")
            
        notas_input = st.text_area("📝 Notas (Opcional):", key="agenda_reg_notas")

        st.write("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            btn_guardar = st.button("💾 Guardar Cliente", type="primary", use_container_width=True)
            
        with col_btn2:
            # Vinculamos la función de limpieza al callback on_click
            st.button("🧹 Limpiar Formulario", type="secondary", use_container_width=True, on_click=limpiar_formulario_agenda)

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
                elif not re.search(r'\d+', tda_num_defecto):
                    st.error("❌ No se detectó un N° de Sucursal válido. El sistema no puede cruzar el inventario.")
                    puede_guardar = False
                else:
                    # --- ESCUDO DE INVENTARIO ABSOLUTO ---
                    # Un error de validación NUNCA se interpreta como ausencia de producto.
                    try:
                        tienda_id_int = int(re.search(r'\d+', tda_num_defecto).group())
                        resultado_inventario = validar_inventario_local(
                            tienda_id_int, modelo_input, talla_input
                        )

                        if resultado_inventario == 'EXISTE':
                            st.error(
                                f"⛔ ¡ALTO! El modelo {modelo_input.upper()} "
                                f"(Talla {talla_input}) SÍ tiene existencia física "
                                f"en la sucursal {tienda_id_int}. Ve a bodega y entrégalo al cliente."
                            )
                            puede_guardar = False

                        elif resultado_inventario == 'ERROR':
                            st.error(
                                "⚠️ No fue posible validar el inventario de esta talla. "
                                "Por seguridad, el sistema NO permitirá registrar el quiebre. "
                                "Revisa que Ventas.xlsx y Valores de tallas.xlsx estén cargados correctamente."
                            )
                            puede_guardar = False
                    except Exception as e:
                        st.error(f"Error técnico en el cruce de inventario. No se guardó el registro: {e}")
                        puede_guardar = False

            if puede_guardar:
                fecha_hoy = (datetime.datetime.utcnow() - datetime.timedelta(hours=6)).strftime("%d/%m/%Y")
                
                fila_nueva = [
                    fecha_hoy, sucursal_input, cliente_input, whatsapp_input, 
                    modelo_input.upper(), str(talla_input), notas_input, "ESPERANDO", motivo_input
                ]
                
                try:
                    sheet_agenda.append_row(fila_nueva)

                    # Actualizamos la copia local después del append para evitar una lectura completa inmediata.
                    datos_local = [list(fila) for fila in st.session_state.get('agenda_datos_cache', datos)]
                    if not datos_local:
                        datos_local = [['Fecha', 'Sucursal', 'Cliente', 'Whatsapp', 'Modelo', 'Talla', 'Notas', 'Estatus', 'Motivo']]
                    datos_local.append(fila_nueva)
                    st.session_state.agenda_datos_cache = datos_local
                    invalidar_cache_agenda()

                    st.success(f"✅ ¡Cliente {cliente_input} registrado exitosamente bajo el motivo: {motivo_input.split(' ')[1]}!")
                    st.info("💡 Formulario guardado. Presiona 'Limpiar Formulario' para borrar estos datos y registrar uno nuevo.")
                except Exception as e:
                    st.error(f"❌ Error al guardar en la nube: {e}")
