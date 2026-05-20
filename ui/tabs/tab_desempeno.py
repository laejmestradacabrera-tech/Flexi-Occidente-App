import streamlit as st
import pandas as pd

def renderizar(archivo_conv):
    st.subheader("📊 Semáforo Comercial de la Zona Occidente")
    st.write("Seguimiento en tiempo real de la Conversión y el Ticket Promedio (unidades de calzado) por sucursal.")
    
    if archivo_conv is not None:
        try:
            df = pd.read_excel(archivo_conv) if str(archivo_conv).endswith('.xlsx') else pd.read_csv(archivo_conv)
            
            col_tienda = df.columns[0]
            col_conv = next((c for c in df.columns if 'convers' in c.lower() or 'conv' in c.lower()), None)
            col_ticket = next((c for c in df.columns if 'ticket' in c.lower() or 'tkt' in c.lower() or 'upt' in c.lower()), None)
            
            if col_conv and col_ticket:
                df[col_tienda] = df[col_tienda].astype(str).str.strip()
                df_limpio = df[~df[col_tienda].str.contains('3004|3015|Total|TOTAL|Resumen', na=False)].copy()
                
                df_limpio[col_conv] = pd.to_numeric(df_limpio[col_conv], errors='coerce')
                df_limpio[col_ticket] = pd.to_numeric(df_limpio[col_ticket], errors='coerce')
                
                def aplicar_semaforo(row):
                    valor_conv = row[col_conv]
                    val_eval = valor_conv * 100 if valor_conv < 1 else valor_conv
                    
                    if val_eval >= 10.90:
                        return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row)
                    elif val_eval >= 9.50:
                        return ['background-color: #fff3cd; color: #856404; font-weight: bold;'] * len(row)
                    else:
                        return ['background-color: #f8d7da; color: #721c24; font-weight: bold;'] * len(row)
                
                df_ordenado = df_limpio.sort_values(by=col_conv, ascending=False).reset_index(drop=True)
                
                st.table(df_ordenado.style.apply(aplicar_semaforo, axis=1).format({
                    col_conv: '{:.2%}' if df_ordenado[col_conv].max() <= 1 else '{:.2f}%',
                    col_ticket: '{:.2f}'
                }))
            else:
                st.warning("⚠️ No se encontraron las columnas de 'Conversión' o 'Ticket' en el archivo.")
        except Exception as e:
            st.error(f"⚠️ Error en pestaña de desempeño: {e}")
    else:
        st.info("📌 Archivo de Conversión no detectado.")
