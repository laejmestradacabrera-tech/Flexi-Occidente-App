import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA (Debe ser la primera línea)
st.set_page_config(
    page_title="Bitácora Ejecutiva - Flexi OI26",
    page_icon="👞",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. ESTILOS VISUALES (Diseño Ejecutivo Dark Mode)
st.markdown("""
    <style>
    /* Fondo principal y textos */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Estilo de las tarjetas de KPI (Métricas) */
    div[data-testid="metric-container"] {
        background-color: #1e293b;
        padding: 15px 20px;
        border-radius: 10px;
        border-left: 5px solid #deff9a;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Color del valor del KPI */
    div[data-testid="stMetricValue"] { color: #deff9a; font-weight: bold; }
    
    /* Ocultar menú de hamburguesa y footer de Streamlit para más limpieza */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. DATOS DE PRUEBA (Mientras conectas Google Sheets)
# Nota para Jose: Cuando tengas el Google Sheets listo, borrarás la función "cargar_datos()"
# y usarás la conexión real a tu archivo.

@st.cache_data
def cargar_datos():
    data = {
        "Fecha": ["25/06/2026", "25/06/2026", "25/06/2026", "26/06/2026", "26/06/2026", "27/06/2026", "27/06/2026", "28/06/2026"],
        "Tienda": [
            "Tienda 98 Plaza del Sol", "Tienda 109 Galerias Guadalajara", "Tienda 98 Plaza del Sol",
            "Tienda 109 Galerias Guadalajara", "Tienda 98 Plaza del Sol", "Tienda 109 Galerias Guadalajara",
            "Tienda 98 Plaza del Sol", "Tienda 109 Galerias Guadalajara"
        ],
        "Nombre": ["GRECYA", "CASIOPEA", "MARLA", "ASTURIAS", "WENNDY", "ATLA", "ZARITA", "KINDRA"],
        "Producto": ["104936 BEIGE", "105125 BURGUNDY", "143802 NEGRO", "143901 COGNAC", "143601 BLANCO", "138604 TAUPE", "144001 NEGRO", "141204 BEIGE"],
        "Comentarios": [
            "A la clienta le encantó el diseño pero no nos llegó talla 24. Se fue sin comprar.",
            "Se vendió muy rápido. Les gusta mucho el color burgundy para esta temporada.",
            "Se lo probaron pero lo sintieron un poco estrecho del empeine. Modelo muy duro.",
            "Cliente buscaba talla 25, se fue sin comprar. Faltó surtido en ese número.",
            "Excelente modelo, muy cómodo. Venta concretada de inmediato.",
            "El color taupe está gustando mucho. Cliente compró dos pares.",
            "Preguntan mucho por él, pero el precio se les hace un poco elevado.",
            "No tenemos surtido de la talla 23 ni 24, perdimos 3 ventas hoy por eso."
        ]
    }
    return pd.DataFrame(data)

df = cargar_datos()

# 4. INTELIGENCIA AUTOMÁTICA (Analiza el texto y asigna estatus)
def clasificar_comentario(texto):
    texto_lower = str(texto).lower()
    if any(palabra in texto_lower for palabra in ["talla", "surtido", "llegó", "falta"]):
        return "🚨 Riesgo de Surtido"
    elif any(palabra in texto_lower for palabra in ["vendi", "venta", "compr", "encantó"]):
        return "✅ Éxito / Venta"
    elif any(palabra in texto_lower for palabra in ["estrecho", "duro", "elevado", "no le gustó"]):
        return "⚠️ Alerta de Producto"
    else:
        return "ℹ️ Observación"

# Aplicamos la clasificación a una nueva columna
df["Status_IA"] = df["Comentarios"].apply(clasificar_comentario)

# 5. ESTRUCTURA DE LA PÁGINA
st.title("👞 Bitácora Ejecutiva: Modelos Importados OI26")
st.markdown("Monitor en **tiempo real** de feedback de clientes en piso de venta. *Periodo: Hasta 3 de Agosto.*")
st.markdown("---")

# 6. MÉTRICAS (KPIs)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total de Interacciones", value=len(df))
with col2:
    ventas = len(df[df["Status_IA"] == "✅ Éxito / Venta"])
    st.metric(label="Comentarios de Venta", value=ventas)
with col3:
    tallas = len(df[df["Status_IA"] == "🚨 Riesgo de Surtido"])
    st.metric(label="Alertas Falta de Talla", value=tallas)
with col4:
    hora_actual = datetime.now().strftime("%H:%M")
    st.metric(label="Última Actualización", value=hora_actual)

st.write("") # Espacio en blanco

# 7. FILTROS
st.subheader("🔍 Filtrar Información")
f_col1, f_col2 = st.columns(2)

with f_col1:
    lista_tiendas = df["Tienda"].unique().tolist()
    tienda_seleccionada = st.multiselect("Seleccionar Tienda", options=lista_tiendas, placeholder="Todas las tiendas")

with f_col2:
    lista_modelos = df["Nombre"].unique().tolist()
    modelo_seleccionado = st.multiselect("Filtrar por Modelo", options=lista_modelos, placeholder="Todos los modelos")

# Aplicar lógica de filtros
df_filtrado = df.copy()
if tienda_seleccionada:
    df_filtrado = df_filtrado[df_filtrado["Tienda"].isin(tienda_seleccionada)]
if modelo_seleccionado:
    df_filtrado = df_filtrado[df_filtrado["Nombre"].isin(modelo_seleccionado)]

st.write("") # Espacio en blanco

# 8. TABLA DE DATOS
st.subheader("📋 Registro de Observaciones en Piso")

if df_filtrado.empty:
    st.info("No hay registros que coincidan con los filtros seleccionados.")
else:
    # Ordenar columnas para visualización
    columnas_mostrar = ["Fecha", "Tienda", "Nombre", "Producto", "Status_IA", "Comentarios"]
    
    st.dataframe(
        df_filtrado[columnas_mostrar],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fecha": st.column_config.TextColumn("Fecha", width="small"),
            "Tienda": st.column_config.TextColumn("Sucursal", width="medium"),
            "Nombre": st.column_config.TextColumn("Familia/Modelo", width="small"),
            "Producto": st.column_config.TextColumn("Detalle (Color)", width="small"),
            "Status_IA": st.column_config.TextColumn("Análisis Rápido", width="medium"),
            "Comentarios": st.column_config.TextColumn("Voz del Cliente (Literal)", width="large"),
        }
    )

st.caption("Esta información fluye directamente desde el formato de captura en las tiendas 98 y 109.")
