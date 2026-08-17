import streamlit as st
import pandas as pd
import datetime
import urllib.parse
import os
import re
import time

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
    Convierte formatos comerciales (22, 22.5) al valor canónico (220, 225).
    """
    try:
        if t is None or (isinstance(t, float) and pd.isna(t)):
            return ""

        texto = str(t).strip().replace(',', '.')
        if not texto:
            return ""

        f = float(texto)

        if 1 <= f < 100:
            f = round(f * 10)

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
    Valida inventario y devuelve un estado explícito: EXISTE, NO_EXISTE, ERROR.
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

        if not t_buscada or not {'tienda', 'modelo', 'departamento'}.issubset(set(df_v.columns)) or 'valor' not in df_t.columns:
            return 'ERROR'

        tienda_series = pd.to_numeric(
            df_v['tienda'].astype(str).str.extract(r'(\d+)', expand=False),
            errors='coerce'
        )
        df_v['tienda_int_chk'] = tienda_series.fillna(-1).astype(int)

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

        if df_filtro.empty:
            return 'NO_EXISTE'

        for _, row in df_filtro.iterrows():
            dpto = str(row.get('departamento', '')).strip().lower()
            tallas_row = df_t[df_t['valor'].astype(str).str.strip().str.lower() == dpto]

            if tallas_row.empty:
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

                existencia = row.get(col_ex, 0)
                try:
                    e_num = float(existencia)
                except (TypeError, ValueError):
                    return 'ERROR'

                return 'EXISTE' if e_num > 0 else 'NO_EXISTE'

        return 'NO_EXISTE'

    except Exception as e:
        st.session_state.ultimo_error_inventario = str(e)
        return 'ERROR'

def verificar_inventario_local(tda_int, modelo, talla):
    return validar_inventario_local(tda_int, modelo, talla) == 'EXISTE'

def obtener_existencia_local(tda_int, modelo, talla):
    """Devuelve la existencia física actual de una combinación tienda/modelo/talla."""
    try:
        if 'df_ventas' not in st.session_state or 'df_tallas' not in st.session_state:
            return None

        df_v = st.session_state.df_ventas.copy()
        df_t = st.session_state.df_tallas.copy()
        df_v.columns = df_v.columns.astype(str).str.strip().str.lower()
        df_t.columns = df_t.columns.astype(str).str.strip().str.lower()

        mod_cln = str(modelo).replace(' ', '').replace('-', '').upper()
        t_buscada = clean_talla(talla)
        if not t_buscada or not {'tienda', 'modelo', 'departamento'}.issubset(df_v.columns) or 'valor' not in df_t.columns:
            return None

        tienda_series = pd.to_numeric(df_v['tienda'].astype(str).str.extract(r'(\d+)', expand=False), errors='coerce')
        df_v['tienda_int_chk'] = tienda_series.fillna(-1).astype(int)

        modelos_norm = df_v['modelo'].astype(str).str.replace(' ', '', regex=False).str.replace('-', '', regex=False).str.upper()

        df_filtro = df_v[(df_v['tienda_int_chk'] == int(tda_int)) & (modelos_norm == mod_cln)]

        if df_filtro.empty:
            return 0.0

        existencia_total = 0.0
        talla_encontrada = False

        for _, row in df_filtro.iterrows():
            dpto = str(row.get('departamento', '')).strip().lower()
            tallas_row = df_t[df_t['valor'].astype(str).str.strip().str.lower() == dpto]
            if tallas_row.empty:
                return None

            for i in range(1, 16):
                col_ex = f'ex{i}'
                if col_ex not in tallas_row.columns or col_ex not in row.index:
                    continue

                val_matriz = tallas_row.iloc[0].get(col_ex, '')
                if pd.isna(val_matriz) or str(val_matriz).strip() == '':
                    continue

                if clean_talla(val_matriz) != t_buscada:
                    continue

                talla_encontrada = True
                try:
                    existencia_total += float(row.get(col_ex, 0) or 0)
                except (TypeError, ValueError):
                    return None
                break

        return existencia_total if talla_encontrada else 0.0

    except Exception as e:
        st.session_state.ultimo_error_inventario = str(e)
        return None

def extraer_existencia_inicial(notas):
    """Extrae la existencia registrada en la "foto" original de las notas."""
    texto = str(notas or '')
    match = re.search(
        r'EXISTENCIA_REGISTRO\s*=\s*([0-9]+(?:\.[0-9]+)?)',
        texto,
        flags=re.IGNORECASE
    )
    if not match:
        return None

    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return None

def recepcion_confirmada(notas):
    """True cuando la tienda confirmó que la nueva unidad ya fue recibida físicamente."""
    return '[RECEPCION_CONFIRMADA]' in str(notas or '').upper()


def actualizar_nota_fila(sheet_agenda, datos, fila_idx_cero_based, nueva_nota):
    """Actualiza Notas usando su encabezado real y sincroniza la copia local."""
    encabezados = [str(c).strip().lower() for c in (datos[0] if datos else [])]
    if 'notas' not in encabezados:
        raise ValueError("La hoja Agenda_Clientes no contiene la columna 'Notas'.")

    col_notas = encabezados.index('notas') + 1
    sheet_agenda.update_cell(fila_idx_cero_based + 2, col_notas, nueva_nota)

    datos_local = [list(fila) for fila in st.session_state.get('agenda_datos_cache', datos)]
    fila_local = fila_idx_cero_based + 1
    col_local = col_notas - 1
    if 0 <= fila_local < len(datos_local):
        while len(datos_local[fila_local]) <= col_local:
            datos_local[fila_local].append('')
        datos_local[fila_local][col_local] = nueva_nota
        st.session_state.agenda_datos_cache = datos_local
        invalidar_cache_agenda()


def limpiar_formulario_agenda():
    st.session_state["agenda_reg_motivo"] = "📦 Falta de Talla (Quiebre)"
    st.session_state["agenda_reg_cliente"] = ""
    st.session_state["agenda_reg_telefono"] = ""
    # Protegemos la limpieza si estos widgets no se renderizaron (Por si eligieron Agenda)
    if "agenda_reg_modelo" in st.session_state:
        st.session_state["agenda_reg_modelo"] = ""
    if "agenda_reg_talla" in st.session_state:
        st.session_state["agenda_reg_talla"] = 25.0
    st.session_state["agenda_reg_notas"] = ""

def limpiar_vista_agenda():
    st.session_state["filtro_sucursal_agenda"] = "👉 Selecciona tu sucursal..."
    st.session_state["ultimo_filtro_agenda"] = "👉 Selecciona tu sucursal..."
    st.session_state["clave_gerencia_agenda"] = ""

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

    if not forzar and datos_cache is not None and (ahora - ultima_lectura) < AGENDA_CACHE_TTL:
        return datos_cache, None

    try:
        datos = sheet_agenda.get_all_values()

        if len(datos) > 0:
            encabezados = [str(c).strip() for c in datos[0]]
            if 'Motivo' not in encabezados:
                sheet_agenda.update_cell(1, len(datos[0]) + 1, 'Motivo')
                datos[0].append('Motivo')

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
        if datos_cache is not None:
            st.session_state.agenda_cache_error = mensaje
            return datos_cache, mensaje
        st.session_state.agenda_cache_error = mensaje
        return None, mensaje

def invalidar_cache_agenda():
    st.session_state.agenda_cache_timestamp = time.time()

def mostrar_modulo_agenda(client_gs):
    asegurar_inventario_cargado()

    if st.session_state.get('agenda_reg_refresh', False):
        st.session_state.agenda_reg_refresh = False

    st.markdown("<h2 style='color: #4338ca;'>📓 Agenda de Clientes y Recuperación de Ventas</h2>", unsafe_allow_html=True)
    st.write("Registra clientes en piso de venta, cruza faltantes de talla con el inventario y gestiona tu cartera de clientes.")

    df_tdas_global = obtener_catalogo_tiendas()
    nombres_sucursales = ["Sin Sucursales Cargadas"]
    col_nom_global = 'NOMBRE'
    
    if not df_tdas_global.empty:
        col_nom_global = 'NOMBRE' if 'NOMBRE' in df_tdas_global.columns else (df_tdas_global.columns[1] if len(df_tdas_global.columns) > 1 else df_tdas_global.columns[0])
        nombres_sucursales = sorted(df_tdas_global[col_nom_global].dropna().astype(str).unique().tolist())
        nombres_sucursales = [n for n in nombres_sucursales if n.strip() != '']

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
            st.error("⏳ Google Sheets alcanzó temporalmente el límite de lecturas. No se realizó ninguna modificación. Espera unos segundos y vuelve a entrar al módulo.")
        else:
            st.error(f"❌ Error al leer Google Sheets. Detalles: {error_lectura}")
        return

    if error_lectura and '429' in str(error_lectura):
        st.warning("⚠️ Google Sheets está limitando temporalmente las lecturas. El sistema está trabajando con la última copia disponible.")

    opcion_default = "👉 Selecciona tu sucursal..."
    opcion_gerencia = "Todas las Sucursales (Solo Gerencia)"
    lista_sucursales_menu = [opcion_default, opcion_gerencia] + nombres_sucursales

    tab_alertas, tab_registro = st.tabs(["🚨 Panel de Alertas y Seguimiento", "📝 Nuevo Registro en Piso"])

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

        if sucursal_filtro == opcion_default:
            st.info("👆 Por favor, selecciona tu sucursal en el menú superior para cargar tu agenda.")
        else:
            st.button("🧹 Limpiar Pantalla / Cerrar Vista", use_container_width=True, type="secondary", on_click=limpiar_vista_agenda)
                
            st.write("<br>", unsafe_allow_html=True)
            
            mostrar_tablero = True
            
            if sucursal_filtro == opcion_gerencia:
                col_clave, col_btn = st.columns([1, 2])
                with col_clave:
                    clave_ingresada = st.text_input("🔐 Clave de Autorización:", type="password", key="clave_gerencia_agenda")
                with col_btn:
                    st.write("<br>", unsafe_allow_html=True)
                    st.button("Validar Acceso", type="primary", key="btn_validar_agenda")
                
                # Validación dura con strip para ignorar espacios accidentales
                clave_maestra = "Flexi2026"
                if clave_ingresada.strip() != clave_maestra:
                    st.warning("🔒 Vista restringida. Ingresa la clave corporativa y presiona Validar Acceso para ver el tablero global.")
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

                    df_faltas = df_pendientes[
                        df_pendientes['Motivo'].astype(str).str.contains(r'Falta|No Vendible', case=False, na=False, regex=True)
                    ]
                    
                    if df_faltas.empty:
                        st.success(f"✨ No tienes registros de quiebres pendientes para {sucursal_filtro}.")
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
                                        notas = str(row.get('Notas', ''))

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

                                        motivo_registro = str(row.get('Motivo', '📦 Falta de Talla'))
                                        es_no_vendible = ('NO_VENDIBLE' in notas.upper() or 'NO VENDIBLE' in motivo_registro.upper())
                                        confirmada = recepcion_confirmada(notas)

                                        existencia_actual = obtener_existencia_local(tda_num_alerta, modelo, talla)
                                        existencia_registro = extraer_existencia_inicial(notas)

                                        # REGLA: la existencia en sistema NO equivale a recepción física.
                                        # Para cualquier quiebre, el incremento de inventario queda en
                                        # "pendiente de recepción" hasta que la encargada lo confirme.
                                        if existencia_registro is None:
                                            nueva_existencia = existencia_actual is not None and existencia_actual > 0
                                        else:
                                            nueva_existencia = existencia_actual is not None and existencia_actual > existencia_registro

                                        if confirmada and existencia_actual is not None and existencia_actual > 0:
                                            estado_alerta = 'DISPONIBLE'
                                        elif nueva_existencia:
                                            estado_alerta = 'PENDIENTE_RECEPCION'
                                        elif existencia_registro is None and es_no_vendible:
                                            estado_alerta = 'ERROR'
                                        else:
                                            estado_alerta = 'PENDIENTE'

                                        zapato_llegado = estado_alerta == 'DISPONIBLE'

                                        if estado_alerta == 'PENDIENTE_RECEPCION':
                                            encabezado = '🟡 NUEVA EXISTENCIA DETECTADA'
                                            subtitulo = 'Par No Vendible' if es_no_vendible else 'Falta de Talla'
                                            if existencia_registro is not None and existencia_actual is not None:
                                                mensaje = (
                                                    f'El inventario en sistema pasó de {existencia_registro:g} a {existencia_actual:g} par(es). '
                                                    'Aún debes confirmar que la nueva unidad ya fue recibida físicamente en tienda.'
                                                )
                                            else:
                                                mensaje = 'Se detectó existencia en sistema. Aún debes confirmar la recepción física en tienda.'
                                            html_tarjeta = f"""
                                            <div style="padding: 15px; border: 2px solid #f59e0b; background-color: #1e293b; border-radius: 8px 8px 0 0;">
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                                    <span style="color: #f59e0b; font-weight: 900; font-size: 13px; letter-spacing: 1px;">{encabezado}</span>
                                                    <span style="color: #94a3b8; font-size: 11px;">{subtitulo}</span>
                                                </div>
                                                <p style="margin: 0; font-size: 14.5px; color: #f8fafc; line-height: 1.4;">
                                                    <span style="font-size: 13px; color: #38bdf8; font-weight: bold;">📍 Sucursal: {sucursal}</span><br>
                                                    <strong>{cliente}</strong> ({whatsapp})<br>{mensaje}
                                                </p>
                                                {"<p style='margin: 8px 0 0 0; font-size: 12px; color: #94a3b8;'><em>📝 Notas: " + notas + "</em></p>" if notas else ""}
                                            </div>
                                            """
                                        elif es_no_vendible and estado_alerta == 'ERROR':
                                            html_tarjeta = f"""
                                            <div style="padding: 15px; border: 2px solid #ef4444; background-color: #1e293b; border-radius: 8px 8px 0 0;">
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                                    <span style="color: #ef4444; font-weight: 900; font-size: 13px; letter-spacing: 1px;">⚠️ REVISAR REGISTRO</span>
                                                    <span style="color: #94a3b8; font-size: 11px;">Par No Vendible</span>
                                                </div>
                                                <p style="margin: 0; font-size: 14.5px; color: #f8fafc; line-height: 1.4;">
                                                    <span style="font-size: 13px; color: #38bdf8; font-weight: bold;">📍 Sucursal: {sucursal}</span><br>
                                                    El registro tiene la marca NO_VENDIBLE, pero no contiene una foto de inventario. No se puede confirmar llegada.
                                                </p>
                                                {"<p style='margin: 8px 0 0 0; font-size: 12px; color: #94a3b8;'><em>📝 Notas: " + notas + "</em></p>" if notas else ""}
                                            </div>
                                            """
                                        elif zapato_llegado:
                                            html_tarjeta = f"""
                                            <div style="padding: 15px; border: 2px solid #22c55e; background-color: #1e293b; border-radius: 8px 8px 0 0; box-shadow: 0 0 15px rgba(34,197,94,0.3);">
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                                    <span style="color: #22c55e; font-weight: 900; font-size: 13px; letter-spacing: 1px;">🟢 ¡CALZADO EN BODEGA!</span>
                                                    <span style="color: #94a3b8; font-size: 11px;">{"Par No Vendible" if es_no_vendible else "Falta de Talla"}</span>
                                                </div>
                                                <p style="margin: 0; font-size: 14.5px; color: #f8fafc; line-height: 1.4;">
                                                    <span style="font-size: 13px; color: #38bdf8; font-weight: bold;">📍 Sucursal: {sucursal}</span><br>
                                                    Llamar al cliente <strong>{cliente}</strong> al <strong style="color: #fbbf24;">{whatsapp}</strong>.<br>
                                                    El producto fue <strong>confirmado físicamente en tienda</strong> y está disponible para el cliente.
                                                </p>
                                                {"<p style='margin: 8px 0 0 0; font-size: 12px; color: #94a3b8;'><em>📝 Notas: " + notas + "</em></p>" if notas else ""}
                                            </div>
                                            """
                                        else:
                                            html_tarjeta = f"""
                                            <div style="padding: 15px; border: 1px solid #334155; background-color: #0f172a; border-radius: 8px 8px 0 0;">
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                                    <span style="color: #64748b; font-weight: 700; font-size: 12px;">⏳ Esperando llegada...</span>
                                                    <span style="color: #475569; font-size: 11px;">{"Par No Vendible" if es_no_vendible else "Falta de Talla"}</span>
                                                </div>
                                                <p style="margin: 0; font-size: 14.5px; color: #cbd5e1; line-height: 1.4;">
                                                    <span style="font-size: 13px; color: #38bdf8; font-weight: bold;">📍 Sucursal: {sucursal}</span><br>
                                                    <strong>{cliente}</strong> ({whatsapp})<br>Buscando modelo <strong>{modelo}</strong> (Talla {talla}).
                                                </p>
                                                {"<p style='margin: 8px 0 0 0; font-size: 12px; color: #64748b;'><em>📝 Notas: " + notas + "</em></p>" if notas else ""}
                                            </div>
                                            """

                                        st.markdown(html_tarjeta, unsafe_allow_html=True)
                                        
                                        if estado_alerta == 'PENDIENTE_RECEPCION':
                                            if st.button("📦 Confirmar recepción física", key=f"btn_receive_{idx}", use_container_width=True, type="primary"):
                                                try:
                                                    nueva_nota = notas.strip()
                                                    if '[RECEPCION_CONFIRMADA]' not in nueva_nota.upper():
                                                        nueva_nota = f"{nueva_nota} [RECEPCION_CONFIRMADA]".strip()
                                                    actualizar_nota_fila(sheet_agenda, datos, idx, nueva_nota)
                                                    st.toast(f"Recepción confirmada: {modelo} talla {talla}.", icon="📦")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"No se pudo confirmar la recepción física: {e}")

                                        btn_type = "primary" if zapato_llegado else "secondary"
                                        if st.button("✅ Marcar como Contactado", key=f"btn_done_{idx}", use_container_width=True, type=btn_type):
                                            try:
                                                encabezados = [str(c).strip().lower() for c in datos[0]]
                                                if 'estatus' not in encabezados:
                                                    raise ValueError("La hoja Agenda_Clientes no contiene la columna 'Estatus'.")
                                                col_estatus = encabezados.index('estatus') + 1
                                                
                                                sheet_agenda.update_cell(idx + 2, col_estatus, "CONTACTADO")

                                                datos_local = [list(fila) for fila in st.session_state.get('agenda_datos_cache', datos)]
                                                fila_local = idx + 1  
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
                            df_mostrar['SUCURSAL'] = df_directorio['Sucursal']
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

        motivo_input = st.selectbox(
            "📌 Motivo del Registro:",
            [
                "📦 Falta de Talla (Quiebre)",
                "🔴 Par No Vendible (Quiebre)",
                "🏷️ Agenda (Aviso de Promociones)"
            ],
            key="agenda_reg_motivo"
        )
        
        cliente_input = st.text_input("👤 Nombre del Cliente:", key="agenda_reg_cliente")
        whatsapp_input = st.text_input("📱 Teléfono (10 dígitos):", max_chars=10, key="agenda_reg_telefono")
        
        es_quiebre = "Falta" in motivo_input or "No Vendible" in motivo_input
        es_no_vendible_captura = "No Vendible" in motivo_input

        # Variables internas por defecto por si eligen Agenda y desaparecen los recuadros
        modelo_input = ""
        talla_input = 25.0

        # UI Dinámica: Oculta completamente Talla y Modelo si es un simple aviso de agenda
        if es_quiebre:
            col_mod, col_tal = st.columns(2)
            with col_mod:
                modelo_input = st.text_input("👟 Modelo Buscado:", key="agenda_reg_modelo")
            with col_tal:
                talla_input = st.number_input("📏 Talla (Ej. 25, 25.5, 250 o 255):", min_value=1.0, max_value=350.0, step=0.5, value=25.0, key="agenda_reg_talla")
            
            if es_no_vendible_captura:
                st.info("🔴 Par No Vendible: El sistema validará la existencia física actual. Solo se disparará la alerta cuando el número de pares supere la existencia de este momento.")
        else:
            st.info("💡 En modo Agenda (Promociones) no se requiere capturar Modelo ni Talla.")

        notas_input = st.text_area("📝 Notas (Opcional):", key="agenda_reg_notas")

        st.write("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            btn_guardar = st.button("💾 Guardar Cliente", type="primary", use_container_width=True)
            
        with col_btn2:
            st.button("🧹 Limpiar Formulario", type="secondary", use_container_width=True, on_click=limpiar_formulario_agenda)

        if btn_guardar:
            puede_guardar = True
            
            if not cliente_input:
                st.error("⚠️ El nombre del cliente es obligatorio.")
                puede_guardar = False
            elif len(whatsapp_input) < 10 or not whatsapp_input.isdigit():
                st.error("⚠️ El número de Teléfono debe tener 10 dígitos numéricos.")
                puede_guardar = False
                
            existencia_registro = None

            if es_quiebre and puede_guardar:
                if not modelo_input:
                    st.error("⚠️ Para registrar un quiebre debes escribir el Modelo.")
                    puede_guardar = False
                elif not re.search(r'\d+', tda_num_defecto):
                    st.error("❌ No se detectó un N° de Sucursal válido. El sistema no puede cruzar el inventario.")
                    puede_guardar = False
                else:
                    try:
                        tienda_id_int = int(re.search(r'\d+', tda_num_defecto).group())
                        resultado_inventario = validar_inventario_local(tienda_id_int, modelo_input, talla_input)
                        existencia_actual = obtener_existencia_local(tienda_id_int, modelo_input, talla_input)

                        if existencia_actual is None or resultado_inventario == 'ERROR':
                            st.error("⚠️ No fue posible validar el inventario de esta talla. Por seguridad, el sistema NO permitirá registrar el quiebre. Revisa que Ventas.xlsx y Valores de tallas.xlsx estén cargados.")
                            puede_guardar = False
                        else:
                            # FOTO UNIVERSAL: Siempre guardamos la existencia actual, ya sea 0, 1 o más (Fantasmas)
                            existencia_registro = existencia_actual

                            if es_no_vendible_captura and existencia_actual <= 0:
                                st.error(f"⛔ No se puede registrar como Par No Vendible porque el modelo {modelo_input.upper()} (Talla {talla_input}) no tiene existencia física en la sucursal {tienda_id_int}.")
                                puede_guardar = False

                    except Exception as e:
                        st.error(f"Error técnico en el cruce de inventario. No se guardó el registro: {e}")
                        puede_guardar = False

            if puede_guardar:
                fecha_hoy = (datetime.datetime.utcnow() - datetime.timedelta(hours=6)).strftime("%d/%m/%Y")
                
                notas_guardar = notas_input.strip() if notas_input else ""
                
                if es_quiebre and existencia_registro is not None:
                    # Inyectamos la foto universal en el registro para evitar los falsos positivos futuros
                    notas_guardar = f"{notas_guardar} [EXISTENCIA_REGISTRO={existencia_registro:g}]".strip()
                    if es_no_vendible_captura:
                        notas_guardar += " [NO_VENDIBLE]"

                fila_nueva = [
                    fecha_hoy, sucursal_input, cliente_input, whatsapp_input, 
                    modelo_input.upper() if es_quiebre else "", 
                    str(talla_input) if es_quiebre else "", 
                    notas_guardar, "ESPERANDO", motivo_input
                ]
                
                try:
                    sheet_agenda.append_row(fila_nueva)

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
