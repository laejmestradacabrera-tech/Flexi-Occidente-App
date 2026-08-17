import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import time
import re

# Configuración del Sandbox
st.set_page_config(page_title="🤖 Laboratorio IA - Flexi", layout="wide")

st.markdown("""
    <style>
    .ia-bubble {
        background-color: #1e293b;
        border-left: 5px solid #8b5cf6;
        padding: 20px;
        border-radius: 8px;
        color: #f8fafc;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .ia-title {
        color: #a78bfa;
        font-weight: 800;
        font-size: 1.1rem;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-pred {
        font-size: 2rem;
        font-weight: 900;
        color: #10b981;
    }
    .metric-risk {
        font-size: 2rem;
        font-weight: 900;
        color: #ef4444;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos_simulacion():
    """Busca el archivo Comparativo local para alimentar a la IA"""
    archivos = [f for f in os.listdir('.') if 'comparativo' in f.lower() and f.endswith(('.xlsx', '.csv'))]
    if archivos:
        archivo = sorted(archivos)[-1]
        try:
            df = pd.read_excel(archivo) if archivo.endswith('.xlsx') else pd.read_csv(archivo)
            return df
        except Exception:
            pass
    return None

def calcular_prediccion_cierre(pares_actuales, pares_historicos, fecha_inicio_temporada):
    """
    Calcula el 'Run Rate' (Velocidad de venta) para predecir el cierre.
    Asumimos una temporada estándar de 180 días (Ej. Semestre).
    """
    hoy = datetime.datetime.now()
    inicio = pd.to_datetime(fecha_inicio_temporada)
    dias_transcurridos = (hoy - inicio).days
    
    if dias_transcurridos <= 0:
        dias_transcurridos = 1
        
    dias_totales_temporada = 180 
    
    # Velocidad actual: Pares por día
    velocidad_diaria = pares_actuales / dias_transcurridos
    
    # Proyección lineal al final del periodo
    proyeccion_cierre = velocidad_diaria * dias_totales_temporada
    
    # Brecha proyectada contra el año pasado
    brecha_proyectada = proyeccion_cierre - pares_historicos
    
    return int(proyeccion_cierre), int(brecha_proyectada), velocidad_diaria

def generar_diagnostico_ia(tienda, pares_25, pares_26, proyeccion, brecha, velocidad):
    """Traduce los cálculos matemáticos a un diagnóstico gerencial escrito"""
    
    if pares_25 == 0:
        return f"La sucursal {tienda} no cuenta con historial suficiente en 2025 para emitir un diagnóstico comparativo."
        
    crecimiento_actual = ((pares_26 - pares_25) / pares_25) * 100
    
    # Construcción del dictamen basado en reglas de negocio
    if brecha >= 0:
        tono = "🟢 **TENDENCIA POSITIVA ACELERADA**"
        mensaje = (
            f"El algoritmo predictivo indica que la sucursal **{tienda}** cerrará la temporada "
            f"con un aproximado de **{proyeccion:,} pares**, superando la marca histórica de {pares_25:,} pares. "
            f"Actualmente la tienda despliega un ritmo de **{velocidad:.1f} pares diarios**. "
            f"La recomendación es proteger el catálogo Top 20 para no frenar esta inercia de crecimiento."
        )
    elif crecimiento_actual < 0 and brecha > -50:
        tono = "🟡 **DESACELERACIÓN MODERADA (RECUPERABLE)**"
        mensaje = (
            f"Alerta preventiva para **{tienda}**. Aunque actualmente presenta un rezago, la proyección de cierre "
            f"({proyeccion:,} pares) sugiere que terminará muy cerca del objetivo histórico ({pares_25:,} pares), "
            f"faltando apenas {abs(brecha)} pares. Se requiere una intervención en el piso de venta centrada en "
            f"incrementar el **Ticket Promedio** (Venta cruzada) para cerrar la brecha matemática."
        )
    else:
        tono = "🔴 **RIESGO CRÍTICO DE CONTRACCIÓN**"
        mensaje = (
            f"Dictamen de alto riesgo para **{tienda}**. El ritmo de venta actual ({velocidad:.1f} pares/día) "
            f"es matemáticamente insuficiente. De mantenerse esta tendencia, la tienda proyecta cerrar con **{proyeccion:,} pares**, "
            f"dejando un déficit severo de **{abs(brecha):,} pares** frente al año anterior. "
            f"Se sugiere una auditoría presencial urgente para revisar exhibición, faltantes de tallas extremas y conversión del personal."
        )
        
    html = f"""
    <div class="ia-bubble">
        <div class="ia-title"><i class="fa-solid fa-robot"></i> Dictamen del Agente Predictivo</div>
        <div style="font-size: 1.1rem; margin-bottom: 10px;">{tono}</div>
        <p style="font-size: 15px; line-height: 1.6; margin: 0;">{mensaje}</p>
    </div>
    """
    return html

st.title("🤖 Laboratorio B2B: Agente Predictivo (Sandbox)")
st.write("Este es un entorno seguro para probar las proyecciones matemáticas antes de inyectarlas al Monitor Comercial.")

df_comp = cargar_datos_simulacion()

if df_comp is not None:
    # Limpieza rápida para el laboratorio
    c_ano = next((c for c in df_comp.columns if 'año' in c.lower() or 'ano' in c.lower()), df_comp.columns[0])
    c_tda = next((c for c in df_comp.columns if 'tienda' in c.lower() or 'sucursal' in c.lower()), df_comp.columns[2])
    c_prs = next((c for c in df_comp.columns if 'pares' in c.lower() or 'cant' in c.lower()), None)
    
    if c_prs:
        df_comp['TIENDA_ID'] = df_comp[c_tda].astype(str).str.extract(r'(\d+)', expand=False)
        df_comp['ANIO_ID'] = pd.to_numeric(df_comp[c_ano], errors='coerce').astype('Int64')
        df_comp[c_prs] = pd.to_numeric(df_comp[c_prs], errors='coerce').fillna(0)
        
        # Consolidar pares por tienda y año
        resumen = df_comp.groupby(['TIENDA_ID', 'ANIO_ID'])[c_prs].sum().unstack(fill_value=0)
        
        # Filtramos tiendas basura
        tiendas_validas = [t for t in resumen.index if pd.notna(t) and t not in ['3004', '3015']]
        
        col_ctrl, col_dash = st.columns([1, 2])
        
        with col_ctrl:
            st.markdown("### 🎛️ Centro de Comando")
            tienda_sel = st.selectbox("Selecciona una sucursal para analizar:", tiendas_validas)
            
            # Simulamos que la temporada empezó el 1 de Enero
            fecha_inicio = st.date_input("Fecha de inicio de Temporada", datetime.date(2026, 1, 1))
            
            analizar_btn = st.button("🧠 Ejecutar Análisis Predictivo", type="primary", use_container_width=True)
            
        with col_dash:
            if analizar_btn:
                with st.spinner("Procesando histórico, calculando velocidad de rotación y proyectando cierre..."):
                    time.sleep(1.5) # Efecto dramático de que la IA está "pensando"
                    
                    p2025 = int(resumen.loc[tienda_sel].get(2025, 0))
                    p2026 = int(resumen.loc[tienda_sel].get(2026, 0))
                    
                    proy_pares, brecha_proy, vel = calcular_prediccion_cierre(p2026, p2025, fecha_inicio)
                    
                    # Panel de Resultados Matemáticos
                    st.markdown("### 📊 Proyección Matemática (Run Rate)")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Histórico (Temp. Ant.)", f"{p2025:,}")
                    c2.metric("Acumulado Actual", f"{p2026:,}", f"{((p2026-p2025)/p2025*100):.1f}%" if p2025>0 else "0%")
                    
                    color_proy = "normal" if brecha_proy >= 0 else "inverse"
                    c3.metric("Predicción Cierre Temp.", f"{proy_pares:,}", f"{brecha_proy:+,} pares", delta_color=color_proy)
                    
                    st.write("<hr>", unsafe_allow_html=True)
                    
                    # Llamada a la voz de la IA
                    diagnostico_html = generar_diagnostico_ia(tienda_sel, p2025, p2026, proy_pares, brecha_proy, vel)
                    st.markdown(diagnostico_html, unsafe_allow_html=True)
                    
else:
    st.warning("⚠️ Necesitas cargar el archivo 'Comparativo por Operacion.xlsx' en tu carpeta para que la IA tenga datos históricos que analizar.")
