with tab2:
    if archivo_modelos:
        df_m = pd.read_excel(archivo_modelos)
        
        # --- LIMPIEZA DE DATOS ---
        col_t = next((c for c in df_m.columns if 'Tienda' in c or 'TIENDA' in c), df_m.columns[0])
        col_mod = next((c for c in df_m.columns if 'Modelo' in c or 'Estilo' in c or 'Art' in c), df_m.columns[1])
        col_cant = next((c for c in df_m.columns if 'Cant' in c or 'Pares' in c or 'Venta' in c), df_m.columns[2])
        col_prov = next((c for c in df_m.columns if 'Prov' in c or 'PROV' in c), None)

        # 1. Filtros de Calzado (Proveedores y Modelos Administrativos)
        if col_prov:
            df_m = df_m[~df_m[col_prov].astype(str).isin(['415', '426', '427'])]
        df_m = df_m[df_m[col_mod].astype(str) != 'AUBOLPETT0RO']
        df_m = df_m[~df_m[col_t].astype(str).str.contains('3004|3015', na=False)]

        # --- CORRECCIÓN DE CONTEO (SUMA POR GRUPO) ---
        # Agrupamos por Tienda y Modelo para asegurar que la suma sea única por artículo
        df_agrupado = df_m.groupby([col_t, col_mod])[col_cant].sum().reset_index()

        # --- VISUALIZACIÓN ---
        tiendas = sorted(df_agrupado[col_t].unique())
        tienda_sel = st.selectbox("Selecciona Tienda para ver el Top de Modelos:", tiendas)
        
        # Filtrar por la tienda seleccionada
        df_tienda = df_agrupado[df_agrupado[col_t] == tienda_sel].copy()
        
        # Sacar el Top 20 real
        top_20 = df_tienda[[col_mod, col_cant]].sort_values(by=col_cant, ascending=False).head(20)
        top_20.columns = ['Modelo / Estilo', 'Pares Vendidos']
        
        st.subheader(f"👟 Top 20 Calzado más vendido - Tienda {tienda_sel}")
        st.table(top_20)
        
        # Verificación rápida para ti
        if str(tienda_sel) == '56':
            st.info(f"💡 Verificación Tienda 56: El modelo CD14201T0NE ahora tiene un conteo agrupado de: {df_tienda[df_tienda[col_mod]=='CD14201T0NE'][col_cant].sum()} pares.")
            
    else:
        st.info("ℹ️ Sube un archivo con la palabra 'Modelos' en GitHub.")
