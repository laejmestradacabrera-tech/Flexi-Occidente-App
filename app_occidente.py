import streamlit as st
import pandas as pd
import numpy as np

# ==============================================================================
# 1. CONFIGURACIÓN INICIAL DE LA PÁGINA Y NAVEGACIÓN
# ==============================================================================
st.set_page_config(page_title="Monitor Comercial - Zona Occidente", layout="wide")

# Menú de navegación con TODAS las pestañas ganadas anteriormente
opcion_menu = st.sidebar.radio(
    "📊 MENÚ PRINCIPAL MONITOR COMERCIAL",
    [
        "📈 Desempeño Comercial General",
        "👟 Optimización y Balanceo (Nivelación)",
        "🔎 Análisis de Conversión por Tienda"
    ]
)

# Perfiles de sucursales autorizados por José Estrada
TIENDAS_MIXTAS = [19, 56, 59, 125, 133]
TIENDA_OUTLET = [12]

# ==============================================================================
# PESTAÑA 1: DESEMPEÑO COMERCIAL GENERAL (RECUPERADA)
# ==============================================================================
if opcion_menu == "📈 Desempeño Comercial General":
    st.title("📈 DESEMPEÑO COMERCIAL - ZONA OCCIDENTE")
    st.write("Visualización estratégica de KPI regionales, ventas globales y cumplimiento de metas.")
    
    # Aquí va tu lógica previa de visualización de KPI Generales (Power BI / Dataframes consolidados)
    st.info("💡 Sección de indicadores comerciales generales, ticket promedio por calzado y tasas de conversión globales activos.")

# ==============================================================================
# PESTAÑA 2: OPTIMIZACIÓN Y BALANCEO DE STOCK (NIVELACIÓN AUTOMÁTICA)
# ==============================================================================
elif opcion_menu == "👟 Optimización y Balanceo (Nivelación)":
    st.title("👟 OPTIMIZACIÓN Y BALANCEO DE STOCK (NIVELACIÓN)")
    st.write("Análisis quirúrgico por talla y estatus con conexión directa al repositorio maestro.")

    # --- ENLACE DIRECTO AUTOMÁTICO A TU ARCHIVO EN GITHUB ---
    # REEMPLAZA ESTA URL por el enlace "Raw" de tu archivo fijo en GitHub
    URL_GITHUB_MAESTRO = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPOSITORIO/main/ventas_existencia_pedidos_occidente.csv"
    
    try:
        # Carga inmediata al hacer clic en la pestaña
        df = pd.read_csv(URL_GITHUB_MAESTRO)
        
        # Procesamiento y Limpieza (El ERP ya envía 0 en vez de NULL)
        df.fillna(0, inplace=True)
        df['Tienda'] = df['Tienda'].astype(int)
        
        # Filtrar las 19 sucursales reales de la Zona Occidente (Excluyendo 3004 y 3015)
        df = df[~df['Tienda'].isin([3004, 3015])]
        
        # Diccionario Maestro de Corrida de Tallas por Prefijo
        def obtener_talla_real(modelo, num_columna):
            mod_str = str(modelo).upper()
            if any(mod_str.startswith(pre) for pre in ['CD', 'CK', 'CY', 'MD', 'VD']):
                tallas_dama = {1:'22', 2:'22.5', 3:'23', 4:'23.5', 5:'24', 6:'24.5', 7:'25', 8:'25.5', 9:'26', 10:'26.5', 11:'27'}
                return tallas_dama.get(num_columna, "Ext.")
            elif any(mod_str.startswith(pre) for pre in ['CH', 'MH', 'VH']):
                tallas_hombre = {1:'25', 2:'25.5', 3:'26', 4:'26.5', 5:'27', 6:'27.5', 7:'28', 8:'28.5', 9:'29', 10:'29.5', 11:'30', 12:'30.5', 13:'31'}
                return tallas_hombre.get(num_columna, "Ext.")
            elif mod_str.startswith('NM'):
                tallas_nm = {1:'17', 2:'17.5', 3:'18', 4:'18.5', 5:'19', 6:'19.5', 7:'20', 8:'20.5', 9:'21'}
                return tallas_nm.get(num_columna, "Ext.")
            elif mod_str.startswith('CJ'):
                tallas_cj = {1:'21.5', 2:'22', 3:'22.5', 4:'23', 5:'23.5', 6:'24', 7:'24.5', 8:'25', 9:'25.5', 10:'26', 11:'26.5', 12:'27'}
                return tallas_cj.get(num_columna, "Ext.")
            return f"T_{num_columna}"

        # Transformación de matriz horizontal a vertical (Unpivot)
        registros_desglosados = []
        for _, fila in df.iterrows():
            modelo = fila['Modelo']
            tienda = int(fila['Tienda'])
            estatus = str(fila['Estatus']).upper()
            
            for i in range(1, 16):
                existencia_fisica = float(fila.get(f'ex{i}', 0))
                pedido_transito = float(fila.get(f'p{i}', 0))
                ventas_acumuladas = float(fila.get(f'v{i}', 0))
                
                stock_disponible = existencia_fisica + pedido_transito
                
                if existencia_fisica > 0 or ventas_acumuladas > 0:
                    talla_nom = obtener_talla_real(modelo, i)
                    registros_desglosados.append({
                        'Tienda': tienda, 'Modelo': modelo, 'Estatus': estatus, 'Talla': talla_nom,
                        'Stock_Fisico': existencia_fisica, 'Disponible': stock_disponible, 'Ventas': ventas_acumuladas
                    })
        
        df_vertical = pd.DataFrame(registros_desglosados)
        
        # Algoritmo de Traspasos con Reglas Directivas Cruzadas (2 meses)
        propuestas_traspaso = []
        for (modelo, talla), grupo in df_vertical.groupby(['Modelo', 'Talla']):
            estatus_mod = grupo['Estatus'].iloc[0]
            
            if estatus_mod in ['S', 'P']:
                orígenes = grupo[(grupo['Stock_Fisico'] >= 1) & (~grupo['Tienda'].isin(TIENDA_OUTLET))]
                destinos = grupo[(grupo['Ventas'] >= 1) & (grupo['Tienda'].isin(TIENDA_OUTLET + TIENDAS_MIXTAS))]
            else:
                orígenes = grupo[(grupo['Stock_Fisico'] >= 2) & (grupo['Ventas'] == 0)]
                destinos = grupo[(grupo['Ventas'] >= 2) & (grupo['Disponible'] == 0)]
            
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
        
        st.success("✅ Datos maestros de la Zona Occidente sincronizados al instante desde GitHub.")
        st.markdown("---")
        st.header("📋 PANEL DE SUPERVISIÓN Y AUDITORÍA DE TRASPASOS")
        
        tienda_sel = st.selectbox("Selecciona una sucursal para auditar sus movimientos de SALIDA:", sorted(df_vertical['Tienda'].unique()))
        
        if not df_propuestas.empty:
            propuestas_tienda = df_propuestas[df_propuestas['Tienda Origen'] == tienda_sel]
            propuestas_tienda_top10 = propuestas_tienda.head(10) # Tope de 10 por tienda
            
            if not propuestas_tienda_top10.empty:
                st.write(f"### 📋 Top 10 Movimientos de Salida Autorizados para Tienda {tienda_sel}")
                st.dataframe(propuestas_tienda_top10[['Tienda Destino', 'Modelo', 'Estatus', 'Talla', 'Pares a Mover', 'Prioridad']], use_container_width=True)
                st.info("💡 Lógica operativa: Las propuestas evacuan saldos hacia el Outlet (12) o Mixtas, protegiendo el producto de línea.")
            else:
                st.info(f"✨ La Tienda {tienda_sel} se encuentra perfectamente nivelada bajo los parámetros actuales.")
        else:
            st.info("El inventario general de la zona está distribuido de forma óptima.")
            
    except Exception as e:
        st.error(f"⚠️ Error de conexión directa. Verifica tu archivo en GitHub y la URL Raw. Detalle técnico: {e}")

# ==============================================================================
# PESTAÑA 3: ANÁLISIS DE CONVERSIÓN POR TIENDA (RECUPERADA)
# ==============================================================================
elif opcion_menu == "🔎 Análisis de Conversión por Tienda":
    st.title("🔎 ANÁLISIS DE CONVERSION POR TIENDA")
    st.write("Auditoría específica de tasas de conversión y ticket promedio calculado estrictamente por unidades de calzado.")
    
    # Aquí va tu lógica de cálculo de conversión de las tiendas
    st.info("💡 Sección de auditoría para indicadores específicos por tienda operativa activa.")
