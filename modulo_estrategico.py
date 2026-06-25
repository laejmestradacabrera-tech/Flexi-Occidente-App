import streamlit as st

# --- CONFIGURACIÓN ---
CLAVE_GERENCIA = "T5604b"

st.set_page_config(page_title="Flexi Occidente", layout="wide")

st.title("🏭 Dashboard Operativo - Flexi Occidente")

# --- CONTROL DE ACCESO ---
st.sidebar.header("🔐 Autenticación")
input_clave = st.sidebar.text_input("Ingresar clave de gerencia:", type="password")

# --- BLOQUE 1: OPERACIONES (Visible para todos) ---
st.subheader("📋 Panel Operativo (Encargado de Tienda)")
with st.container():
    # Aquí puedes insertar tus métricas o tablas operativas actuales
    col1, col2, col3 = st.columns(3)
    col1.metric("Ventas Totales", "$120,000", "5%")
    col2.metric("Inventario en Tienda", "450 pares", "-2")
    col3.metric("Ticket Promedio", "$850")
    st.info("Visualización estándar de operaciones diarias.")

# --- BLOQUE 2: ESTRATÉGICO (Solo Gerencia) ---
if input_clave == CLAVE_GERENCIA:
    st.markdown("---")
    st.subheader("🎯 Módulo de Decisiones Estratégicas")
    st.success("Acceso de Gerencia validado.")
    
    with st.container():
        # Aquí insertas tus gráficos o análisis de alto nivel
        st.write("### Análisis de Rentabilidad y Proyecciones")
        # Ejemplo de espacio para tus gráficas gerenciales
        st.area_chart([10, 20, 30, 40, 50])
        
        col_a, col_b = st.columns(2)
        col_a.write("Distribución de Inventario por Planta")
        col_b.write("Proyección de Ventas a 30 días")
else:
    if input_clave:
        st.sidebar.error("Clave incorrecta. Solo lectura operativa.")
