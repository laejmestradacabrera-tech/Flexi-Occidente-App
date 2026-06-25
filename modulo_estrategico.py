import streamlit as st
from modulo_estrategico import mostrar_modulo_estrategico

st.set_page_config(layout="wide")

# Pestañas
tab1, tab2, tab3 = st.tabs(["Operaciones", "Inventario", "Decisiones Estratégicas"])

with tab1:
    st.write("Vista Operativa")

with tab2:
    st.write("Vista Inventario")

with tab3:
    # AQUÍ ESTÁ LA CONEXIÓN: Llamamos a la función del otro archivo
    mostrar_modulo_estrategico()
