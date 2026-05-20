import streamlit as st
import pandas as pd
import os

# 1. ENLACE EXCLUSIVO CON LA PESTAÑA 1 QUE YA SEPARAMOS
from ui.tabs import tab_desempeno

st.set_page_config(page_title="Monitor Comercial - Zona Occidente", layout="wide")

st.title("🔴 MONITOR COMERCIAL - ZONA OCCIDENTE")
st.markdown(f"**Director de Operaciones:** LAE. José Martín Estrada Cabrera")

# ==============================================================================
# LECTURA DE BASES DE DATOS DESDE GITHUB
# ==============================================================================
def buscar_archivo_local(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith(('.xlsx', '.csv'))]
    return sorted(archivos)[-1] if archivos else None

arch_conv = buscar_archivo_local('Conversion')
arch_comp = buscar_archivo_local('Comparativo por Operacion')
arch_mod = buscar_archivo_local('Venta_Modelos')

# ==============================================================================
# MANTENEMOS LAS 7 PESTAÑAS EN EL ORDEN EXACTO DE TU MONITOR
# ==============================================================================
(tab_desem_pestana, tab_comp_pestana, tab_top_tienda, 
 tab_top_zona, tab_ruta, tab_cap_pestana, tab_nivelacion) = st.tabs([
    "📊 DESEMPEÑO COMERCIAL", 
    "📈 COMPARATIVO MENSUAL", 
    "👟 TOP 20 TIENDA",
    "🌍 TOP 20 ZONA",
    "🧭 RUTA DEL CLIENTE",
    "🎓 CAPACITACIÓN Y PILARES", 
    "🔄 NIVELACIÓN DE STOCK"
])

# ==============================================================================
# CONTENIDOS DE LAS PESTAÑAS
# ==============================================================================

with tab_desem_pestana:
    # MÓDULO SEPARADO CON ÉXITO: Va a ui/tabs/tab_desempeno.py
    tab_desempeno.renderizar(arch_conv)


with tab_comp_pestana:
    st.subheader("Análisis Comparativo de Calzado Mensual")
    if arch_comp is not None:
        try:
            df_op = pd.read_excel(arch_comp) if str(arch_comp).endswith('.xlsx') else pd.read_csv(arch_comp)
            c_ano = next((c for c in df_op.columns if 'año' in c.lower() or 'ano' in c.lower()), df_op.columns[0])
            c_tda = next((c for c in df_op.columns if 'tienda' in c.lower() or 'sucursal' in c.lower()), df_op.columns[2])
            c_prs = next((c for c in df_op.columns if 'pares' in c.lower() or 'cant' in c.lower()), None)
            c_imp = next((c for c in df_op.columns if 'importe' in c.lower() or 'monto' in c.lower()), None)
            
            if c_prs and c_imp:
                df_op[c_tda] = df_op[c_tda].astype(str).str.strip()
                df_op = df_op[~df_op[c_tda].str.contains('3004|3015', na=False)]
                resumen = df_op.groupby([c_tda, c_ano])[[c_prs, c_imp]].sum().unstack(fill_value=0)
                resumen.columns = ['Pares 2025', 'Pares 2026', 'Pesos 2025', 'Pesos 2026']
                resumen = resumen.reset_index()
                st.dataframe(resumen)
        except Exception as e:
            st.error(f"Error en comparativo: {e}")


with tab_top_tienda:
    st.subheader("Top 20 Modelos por Sucursal")
    if arch_mod is not None:
        try:
            df_m = pd.read_excel(arch_mod) if str(arch_mod).endswith('.xlsx') else pd.read_csv(arch_mod)
            col_tda = next((c for c in df_m.columns if 'tienda' in c.lower() or 'sucursal' in c.lower()), df_m.columns[0])
            col_mod = next((c for c in df_m.columns if 'clave' in c.lower() or 'modelo' in c.lower() or 'estilo' in c.lower()), df_m.columns[1])
            col_cant = next((c for c in df_m.columns if 'cant' in c.lower() or 'pza' in c.lower() or 'vta' in c.lower()), df_m.columns[-1])
            
            df_m[col_tda] = df_m[col_tda].astype(str).str.strip()
            df_m = df_m[~df_m[col_tda].str.contains('3004|3015', na=False)]
            
            listado_tiendas = sorted(df_m[col_tda].unique())
            tienda_sel = st.selectbox("Selecciona la Tienda para auditar su Top 20:", listado_tiendas)
            
            df_tda = df_m[df_m[col_tda] == tienda_sel]
            top_20_tda = df_tda.groupby(col_mod)[col_cant].sum().reset_index()
            top_20_tda = top_20_tda.sort_values(by=col_cant, ascending=False).head(20).reset_index(drop=True)
            st.table(top_20_tda)
        except Exception as e:
            st.error(f"Error en Top Tienda: {e}")


with tab_top_zona:
    st.subheader("Top 20 Modelos General - Zona Occidente")
    if arch_mod is not None:
        try:
            df_z = pd.read_excel(arch_mod) if str(arch_mod).endswith('.xlsx') else pd.read_csv(arch_mod)
            col_tda = next((c for c in df_z.columns if 'tienda' in c.lower() or 'sucursal' in c.lower()), df_z.columns[0])
            col_mod = next((c for c in df_z.columns if 'clave' in c.lower() or 'modelo' in c.lower() or 'estilo' in c.lower()), df_z.columns[1])
            col_cant = next((c for c in df_z.columns if 'cant' in c.lower() or 'pza' in c.lower() or 'vta' in c.lower()), df_z.columns[-1])
            
            df_z[col_tda] = df_z[col_tda].astype(str).str.strip()
            df_z = df_z[~df_z[col_tda].str.contains('3004|3015', na=False)]
            
            top_20_zona = df_z.groupby(col_mod)[col_cant].sum().reset_index()
            top_20_zona = top_20_zona.sort_values(by=col_cant, ascending=False).head(20).reset_index(drop=True)
            st.table(top_20_zona)
        except Exception as e:
            st.error(f"Error en Top Zona: {e}")


with tab_ruta:
    st.subheader("Estrategia Operativa: Ruta del Cliente")
    ruta_img = "assets/RC Zona Occidente.png"
    if os.path.exists(ruta_img):
        st.image(ruta_img, caption="Estructura Operativa Comercial - Ruta del Cliente")
    else:
        st.info("📌 Imagen 'RC Zona Occidente.png' lista en visualización de assets.")


with tab_cap_pestana:
    st.subheader("Centro de Capacitación y Desarrollo Operativo")
    opciones_video = {"Mi Nómina Flexi": "https://youtu.be/688Bi49rI30", "Tutorial Vales de Zapatos": "https://youtu.be/6hB95lYcL1g", "Tutorial mi Flexi": "https://youtu.be/WVi8geGSeOg"}
    video_sel = st.selectbox("Material Audiovisual:", list(opciones_video.keys()))
    st.video(opciones_video[video_sel])
    st.markdown("### 📘 Manual de Integración a Tiendas Flexi (7 Pilares)")
    st.write("*(Aquí se despliegan tus textos originales de retención de personal)*")


with tab_nivelacion:
    st.subheader("Nivelación de Stock entre Tiendas")
    st.write("🔐 Módulo en fase de espera - Lógica matemática congelada para análisis.")
