import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE LA PÁGINA (Estilo limpio para celulares en tienda)
st.set_page_config(
    page_title="Captura de Bitácora OI26",
    page_icon="📝",
    layout="centered"
)

# Estilo para hacer el botón más visible y la interfaz más limpia
st.markdown("""
    <style>
    div[data-testid="stForm"] { border: 2px solid #deff9a; border-radius: 10px; padding: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. DICCIONARIO DE DATOS (Extraído de tu archivo Excel)
# Esto vincula cada modelo con sus colores/códigos específicos
catalogo_productos = {
    "GRECYA (1049)": ["104936 BEIGE", "104936 MARINO"],
    "CASIOPEA (1051)": ["105125 BURGUNDY", "105125 NEGRO"],
    "ATLA (1386)": ["138604 NEGRO", "138604 TAUPE"],
    "KINDRA (1412)": ["141204 BEIGE"],
    "DEYRA (1413)": ["141303 NEGRO"],
    "WENNDY (1436)": ["143601 BEIGE", "143601 BLANCO", "143601 NEGRO"],
    "MARLA (1438)": ["143802 BEIGE", "143802 NEGRO"],
    "ASTURIAS (1439)": ["143901 NEGRO", "143901 COGNAC"],
    "ZARITA (1440)": ["144001 NEGRO"]
}

st.title("📝 Registro de Modelos OI26")
st.markdown("Por favor, registra **todos** los comentarios de los clientes sobre la nueva temporada. *(Válido al 3 de Agosto)*")

# 3. CONSTRUCCIÓN DEL FORMULARIO DE CAPTURA
with st.form("form_captura_tienda", clear_on_submit=True):
    
    # Campo 1: Tienda (Solo las 2 que solicitaste)
    tienda = st.selectbox(
        "1. Selecciona tu Sucursal:",
        options=["Tienda 98 Plaza del Sol", "Tienda 109 Galerias Guadalajara"],
        index=None,
        placeholder="Elige tu tienda..."
    )
    
    # Campo 2: Modelo
    modelo = st.selectbox(
        "2. Familia / Nombre del Modelo:",
        options=list(catalogo_productos.keys()),
        index=None,
        placeholder="¿De qué modelo opinó el cliente?"
    )
    
    # Campo 3: Producto / Color
    # Extraemos las opciones dependiendo del modelo seleccionado arriba
    opciones_producto = catalogo_productos[modelo] if modelo else []
    
    producto = st.selectbox(
        "3. Detalle y Color:",
        options=opciones_producto,
        index=None,
        placeholder="Selecciona primero el modelo arriba..." if not modelo else "Elige el color..."
    )
    
    # Campo 4: Comentarios
    comentarios = st.text_area(
        "4. Observaciones y Comentarios del Cliente:",
        placeholder="Ej: Le encantó el diseño pero no llegó talla 24, se fue sin comprar. / Compró el modelo, dice que es muy cómodo.",
        height=150
    )
    
    st.markdown("---")
    
    # Botón de envío
    enviado = st.form_submit_button("📤 Enviar Reporte al Gerente", use_container_width=True)

# 4. LÓGICA DE GUARDADO (Al presionar el botón)
if enviado:
    # Validamos que no envíen campos vacíos
    if not tienda or not modelo or not producto or not comentarios:
        st.error("⚠️ Por favor completa todos los campos antes de enviar.")
    else:
        # Aquí se armaría el paquete de datos para mandarlo a tu Google Sheets
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        datos_capturados = {
            "Fecha": fecha_actual,
            "Tienda": tienda,
            "Modelo": modelo.split(" ")[0], # Quita el número entre paréntesis para que quede limpio
            "Producto": producto,
            "Comentarios": comentarios
        }
        
        # ---------------------------------------------------------
        # NOTA PARA JOSE: Aquí iría tu código de conexión para guardar en Sheets
        # Ej: 
        # df_nuevo = pd.DataFrame([datos_capturados])
        # conn = st.connection("gsheets", type=GSheetsConnection)
        # existing_data = conn.read(worksheet="Bitacora_OI26")
        # updated_data = pd.concat([existing_data, df_nuevo], ignore_index=True)
        # conn.update(worksheet="Bitacora_OI26", data=updated_data)
        # ---------------------------------------------------------
        
        # Mensaje de éxito visual para la encargada
        st.success(f"✅ ¡Gracias! Tu reporte para el modelo {datos_capturados['Modelo']} se envió correctamente.")
        st.balloons() # Pequeña animación de confirmación
