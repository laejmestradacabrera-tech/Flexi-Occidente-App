import streamlit as st
import pandas as pd
import numpy as np
import requests

def mostrar_pestaña_nivelacion_dinamica_github():
    st.title("👟 OPTIMIZACIÓN Y BALANCEO DE STOCK (NIVELACIÓN)")
    st.write("Análisis quirúrgico por talla y estatus con conexión directa al repositorio maestro de la Zona Occidente.")

    # --- CONFIGURACIÓN DE TU REPOSITORIO DE GITHUB ---
    # Reemplaza con tus datos reales de GitHub para que el sistema escanee tu carpeta
    USUARIO_GITHUB = "TU_USUARIO"
    REPOSITORIO = "TU_REPOSITORIO"
    
    # API de GitHub para listar y auto-detectar los archivos del repositorio
    api_url = f"https://api.github.com/repos/{USUARIO_GITHUB}/{REPOSITORIO}/contents/"
    
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            archivos = response.json()
            
            # Filtrar archivos de datos (xlsx o csv) y excluir archivos de código
            archivos_datos = [f for f in archivos if f['name'].endswith(('.xlsx', '.csv'))]
            
            if not archivos_datos:
                st.error("No se encontraron archivos de Excel o CSV en tu repositorio de GitHub.")
                return
            
            # LÓGICA DE FECHA DINÁMICA: Ordena y detecta el archivo modificado más recientemente
            # Esto te permite subir nombres con fecha como 'Inventario_2Meses_170526.csv' y lo leerá solo
            archivos_datos.sort(key=lambda x: x['name'], reverse=True)
            archivo_mas_reciente = archivos_datos[0]
            url_raw = archivo_mas_reciente['download_url']
            nombre_archivo = archivo_mas_reciente['name']
            
            st.success(f"📦 **Archivo maestro detectado e importado desde GitHub:** `{nombre_archivo}`")
            
            # Leer el archivo según su extensión (.xlsx o .csv)
            if nombre_archivo.endswith('.csv'):
                df = pd.read_csv(url_raw)
            else:
                df = pd.read_excel(url_raw)
                
            # --- FASE DE LIMPIEZA Y ESTANDARIZACIÓN (Datos ya vienen con 0 en vez de NULL) ---
            df.fillna(0, inplace=True)
            df['Tienda'] = df['Tienda'].astype(int)
            
            # Filtrar las 19 sucursales reales de la Zona Occidente (Excluyendo 3004 y 3015)
            df = df[~df['Tienda'].isin([3004, 3015])]
            
            # --- CONFIGURACIÓN DE PERFILES DE TIENDA AUTORIZADOS POR JOSÉ ESTRADA ---
            tiendas_mixtas = [19, 56, 59, 125, 133]
            tienda_outlet = [12]
            
            # --- DICCIONARIO MAESTRO DE CORRIDA DE TALLAS ---
            def obtener_talla_real(modelo, num_columna):
                mod_str = str(modelo).upper()
                
                # 1. Dama (CD, CK, CY, MD, VD) -> Tallas del 22 al 27
                if any(mod_str.startswith(pre) for pre in ['CD', 'CK', 'CY', 'MD', 'VD']):
                    tallas_dama = {1:'22', 2:'22.5', 3:'23', 4:'23.5', 5:'24', 6:'24.5', 7:'25', 8:'25.5', 9:'26', 10:'26.5', 11:'27'}
                    return tallas_dama.get(num_columna, "Ext.")
                
                # 2. Caballero (CH, MH, VH) -> Tallas del 25 al 31
                elif any(mod_str.startswith(pre) for pre in ['CH', 'MH', 'VH']):
                    tallas_hombre = {1:'25', 2:'25.5', 3:'26', 4:'26.5', 5:'27', 6:'27.5', 7:'28', 8:'28.5', 9:'29', 10:'29.5', 11:'30', 12:'30.5', 13:'31'}
                    return tallas_hombre.get(num_columna, "Ext.")
                
                # 3. NM (Niños Menores / Preescolar) -> Tallas del 17 al 21 (Niño/Niña)
                elif mod_str.startswith('NM'):
                    tallas_nm = {1:'17', 2:'17.5', 3:'18', 4:'18.5', 5:'19', 6:'19.5', 7:'20', 8:'20.5', 9:'21'}
                    return tallas_nm.get(num_columna, "Ext.")
                
                # 4. CJ (Calzado Juvenil Infantil) -> Tallas del 21.5 al 27 o 25
                elif mod_str.startswith('CJ'):
                    tallas_cj = {1:'21.5', 2:'22', 3:'22.5', 4:'23', 5:'23.5', 6:'24', 7:'24.5', 8:'25', 9:'25.5', 10:'26', 11:'26.5', 12:'27'}
                    return tallas_cj.get(num_columna, "Ext.")
                
                return f"T_{num_columna}"

            # --- PROCESAMIENTO (UNPIVOT: MATRIZ HORIZONTAL A COLUMNA VERTICAL) ---
            registros_desglosados = []
            for _, fila in df.iterrows():
                modelo = fila['Modelo']
                tienda = int(fila['Tienda'])
                estatus = str(fila['Estatus']).upper()
                
                for i in range(1, 16):
                    existencia_fisica = float(fila.get(f'ex{i}', 0))
                    pedido_transito = float(fila.get(f'p{i}', 0))
                    ventas_acumuladas = float(fila.get(f'v{i}', 0))
                    
                    # Fórmula de Inventario Disponible (Limpia con ceros)
                    stock_disponible = existencia_fisica + pedido_transito
                    
                    if existencia_fisica > 0 or ventas_acumuladas > 0:
                        talla_nom = obtener_talla_real(modelo, i)
                        registros_desglosados.append({
                            'Tienda': tienda, 'Modelo': modelo, 'Estatus': estatus, 'Talla': talla_nom,
                            'Stock_Fisico': existencia_fisica, 'Disponible': stock_disponible, 'Ventas': ventas_acumuladas
                        })
            
            df_vertical = pd.DataFrame(registros_desglosados)
            
            # --- ALGORITMO MAESTRO DE GENERACIÓN DE TRASPASOS INTELIGENTES ---
            propuestas_traspaso = []
            for (modelo, talla), grupo in df_vertical.groupby(['Modelo', 'Talla']):
                estatus_mod = grupo['Estatus'].iloc[0]
                
                # REGLAS DIFERENCIADAS DE SALIDA Y DESTINO SEGÚN REQUERIMIENTOS DIRECTIVOS
                if estatus_mod in ['S', 'P']:
                    # Estrategia de Evacuación: Sale de cualquier tienda normal (excepto Outlet)
                    orígenes = grupo[(grupo['Stock_Fisico'] >= 1) & (~grupo['Tienda'].isin(tienda_outlet))]
                    # Destinos autorizados para saldos: Outlet (12) y Mixtas (19, 56, 59, 125, 133) con mayor necesidad
                    destinos = grupo[(grupo['Ventas'] >= 1) & (grupo['Tienda'].isin(tienda_outlet + tiendas_mixtas))]
                else: 
                    # Estrategia Estatus N (Vigente): Nivelación Quirúrgica para cuidar margen
                    orígenes = grupo[(grupo['Stock_Fisico'] >= 2) & (grupo['Ventas'] == 0)]
                    # Va a cualquier sucursal con quiebre de stock disponible y demanda real
                    destinos = grupo[(grupo['Ventas'] >= 2) & (grupo['Disponible'] == 0)]
                
                # Emparejar la necesidad crítica con el stock disponible excedente
                for _, orig_row in orígenes.iterrows():
                    for _, dest_row in destinos.iterrows():
                        cant_mover = min(int(orig_row['Stock_Fisico']), int(dest_row['Ventas']))
                        if cant_mover > 0:
                            propuestas_traspaso.append({
                                'Tienda Origen': int(orig_row['Tienda']),
                                'Tienda Destino': int(dest_row['Tienda']),
                                'Modelo': modelo,
                                'Estatus': estatus_mod,
                                'Talla': talla,
                                'Pares a Mover': cant_mover,
                                'Prioridad': '🚨 CRÍTICA (Quiebre)' if estatus_mod == 'N' else '📦 EVACUACIÓN (Saldo)'
                            })
            
            df_propuestas = pd.DataFrame(propuestas_traspaso)
            
            # --- PANEL DE AUDITORÍA DIRECTIVA DE JOSÉ ESTRADA ---
            st.markdown("---")
            st.header("📋 PANEL DE SUPERVISIÓN Y AUDITORÍA DE TRASPASOS")
            
            # Selector para auditar individualmente cada una de las 19 sucursales activas
            tienda_sel = st.selectbox("Selecciona una sucursal para auditar sus movimientos de SALIDA:", sorted(df_vertical['Tienda'].unique()))
            
            if not df_propuestas.empty:
                propuestas_tienda = df_propuestas[df_propuestas['Tienda Origen'] == tienda_sel]
                
                # TOPE LOGÍSTICO REQUERIDO: Máximo 10 movimientos de salida para proteger la operación de bodega
                propuestas_tienda_top10 = propuestas_tienda.head(10)
                
                if not propuestas_tienda_top10.empty:
                    st.write(f"### 📋 Top 10 Movimientos de Salida Autorizados para Tienda {tienda_sel}")
                    st.dataframe(propuestas_tienda_top10[['Tienda Destino', 'Modelo', 'Estatus', 'Talla', 'Pares a Mover', 'Prioridad']], use_container_width=True)
                    st.info("💡 Lógica activa: Las propuestas están dirigidas estrictamente hacia las tiendas con el perfil de formato autorizado y con mayor necesidad comercial detectada en el histórico de 2 meses.")
                else:
                    st.info(f"✨ Parámetros en orden. La Tienda {tienda_sel} se encuentra balanceada; no requiere generar salidas hoy.")
            else:
                st.info("El inventario general de la zona se encuentra óptimamente distribuido.")
                
        else:
            st.error(f"Error de comunicación con la API de GitHub. Código de estado: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error en la conexión con el repositorio. Asegúrate de actualizar los campos de USUARIO y REPOSITORIO. Detalle técnico: {e}")

# Ejecución de la pestaña dentro del monitor
mostrar_pestaña_nivelacion_dinamica_github()
