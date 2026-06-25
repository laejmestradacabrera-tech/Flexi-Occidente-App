import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
import datetime
from fpdf import FPDF
import openpyxl
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import locale
import subprocess
import streamlit.components.v1 as components 
import re

# Intentamos configurar el idioma español para las fechas
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    pass

# --- CONFIGURACIÓN CENTRALIZADA DE GOOGLE ---
scope = [
    'https://spreadsheets.google.com/feeds', 
    'https://www.googleapis.com/auth/drive', 
    'https://www.googleapis.com/auth/spreadsheets'
]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
    client = gspread.authorize(creds)
    # Conexiones usando el ID
    ID_ARCHIVO = '1lGlVEBgu9QsrH9PYTTuoRKQeWnYiR7OwUElCsfkDgoM'
    archivo_ventas_g = client.open_by_key(ID_ARCHIVO)
    sheet_bitacora = client.open_by_key(ID_ARCHIVO).sheet1
except Exception as e:
    st.warning("Advertencia: No se pudo conectar a Google Sheets. Verifica tus secretos.")

# --- FUNCIONES ---
def obtener_fecha_actualizacion(nombre_archivo):
    if not nombre_archivo: return "Archivo no disponible"
    try:
        comando = ['git', 'log', '-1', '--format=%ct', nombre_archivo]
        resultado = subprocess.run(comando, capture_output=True, text=True)
        if resultado.returncode == 0 and resultado.stdout.strip():
            timestamp_github = int(resultado.stdout.strip())
            fecha_utc = datetime.datetime.utcfromtimestamp(timestamp_github)
            fecha_mexico = fecha_utc - datetime.timedelta(hours=6)
            return fecha_mexico.strftime("%d/%m/%Y - %H:%M hrs")
    except Exception:
        pass 
    try:
        tiempo_modificacion = os.path.getmtime(nombre_archivo)
        fecha_servidor = datetime.datetime.utcfromtimestamp(tiempo_modificacion)
        fecha_mexico = fecha_servidor - datetime.timedelta(hours=6)
        return fecha_mexico.strftime("%d/%m/%Y - %H:%M hrs")
    except FileNotFoundError:
        return "Archivo pendiente de carga"
    except Exception:
        return "Fecha no disponible"

def cargar_tiendas():
    nombre_archivo = "CORREO DE TIENDAS.xlsx"
    try:
        return pd.read_excel(nombre_archivo)
    except Exception as e:
        return pd.DataFrame({'TIENDA': ['Error'], 'NOMBRE': ['Sin datos'], 'ENCARGADO': ['Sin datos']})

def cargar_archivos_locales():
    if 'df_ventas' not in st.session_state or 'df_tallas' not in st.session_state:
        try:
            st.session_state.df_ventas = pd.read_excel("Ventas.xlsx")
            st.session_state.df_tallas = pd.read_excel("Valores de tallas.xlsx")
        except Exception as e:
            return False
    return True

def validar_captura_stock(tienda_id, modelo, talla_input, df_ventas, df_tallas):
    try:
        df_ventas.columns = df_ventas.columns.astype(str).str.strip().str.lower()
        df_tallas.columns = df_tallas.columns.astype(str).str.strip().str.lower()
        
        try: tda_buscada = int(str(tienda_id).strip())
        except: tda_buscada = -1
            
        df_ventas['tienda_int'] = pd.to_numeric(df_ventas['tienda'], errors='coerce').fillna(-1).astype(int)
        
        modelo_buscado = str(modelo).replace(' ', '').replace('-', '').upper()
        df_ventas['modelo_cln'] = df_ventas['modelo'].astype(str).str.replace(' ', '', regex=False).str.replace('-', '', regex=False).str.upper()
        
        df_filtro = df_ventas[(df_ventas['tienda_int'] == tda_buscada) & (df_ventas['modelo_cln'] == modelo_buscado)]
        
        try: talla_buscada_str = str(int(float(talla_input)))
        except: talla_buscada_str = str(talla_input).strip()
            
        with st.expander("🔍 MODO DEPURACIÓN: AUDITORÍA DE CRUCE DE TALLAS", expanded=True):
            st.write(f"**Buscando:** Tienda N°=[{tda_buscada}], Modelo=[{modelo_buscado}], Talla Capturada=[{talla_buscada_str}]")
            
            if df_filtro.empty:
                st.write(f"❌ **Resultado:** El modelo {modelo_buscado} no existe en el inventario de la Tienda {tda_buscada}. (Quiebre válido).")
                return True, ""
                
            st.write(f"✅ Se encontraron {len(df_filtro)} fila(s) del modelo. Cruzando con archivo de Tallas...")
            
            col_dpto = 'valor' if 'valor' in df_tallas.columns else df_tallas.columns[0]
            df_tallas['dpto_cln'] = df_tallas[col_dpto].astype(str).str.strip().str.lower()
            
            for idx, row_venta in df_filtro.iterrows():
                dpto_venta = str(row_venta.get('departamento', '')).strip().lower()
                st.write(f"--- \n**Analizando Departamento:** '{dpto_venta}'")
                tallas_row = df_tallas[df_tallas['dpto_cln'] == dpto_venta]
                
                if tallas_row.empty:
                    st.warning(f"⚠️ No se encontró el departamento '{dpto_venta}' en Valores de tallas.xlsx")
                    continue
                    
                for i in range(1, 16):
                    col_ex = f'ex{i}'
                    if col_ex in tallas_row.columns:
                        talla_matriz = tallas_row.iloc[0][col_ex]
                        if pd.notna(talla_matriz) and str(talla_matriz).strip() != '' and str(talla_matriz).strip().lower() != 'nan':
                            try: talla_matriz_str = str(int(float(talla_matriz)))
                            except: talla_matriz_str = str(talla_matriz).strip()
                                
                            if talla_matriz_str == talla_buscada_str:
                                st.write(f"🎯 **¡COINCIDENCIA ENCONTRADA!** Talla Matriz [{talla_matriz_str}] == Talla Captura [{talla_buscada_str}] en la columna **{col_ex}**")
                                if col_ex in row_venta:
                                    existencia = row_venta[col_ex]
                                    st.write(f"📦 **Existencia leída en Ventas para {col_ex}:** [{existencia}]")
                                    try: existencia_num = float(existencia)
                                    except: existencia_num = 0.0
                                        
                                    if existencia_num > 0:
                                        st.error(f"⛔ BLOQUEO ACTIVADO: Se detectaron {existencia_num} piezas físicas.")
                                        return False, f"⛔ CAPTURA BLOQUEADA: El sistema registra {int(existencia_num)} par(es) de la talla {talla_buscada_str} (Modelo {modelo_buscado}) físicamente en la sucursal {tda_buscada}."
                                    else:
                                        st.write(f"✅ La existencia es {existencia_num}. Permitiendo captura (Quiebre válido).")
                                else:
                                    st.write(f"❌ **ERROR:** La columna [{col_ex}] NO existe en el archivo Ventas.xlsx")
        return True, ""
    except Exception as e:
        st.error(f"Error interno en validación: {e}")
        return True, ""

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Monitor Operativo Flexi Occidente", layout="wide")

# --- ESTILO GLOBAL INTERACTIVO ---
st.markdown("""
    <style>
    .main-title {
        text-align: center; color: #E30613; font-size: 32px; font-weight: bold;
        border-bottom: 3px solid #E30613; padding-bottom: 10px; margin-bottom: 20px;
    }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: white; color: #666; text-align: center;
        padding: 8px; font-size: 13px; border-top: 1px solid #ddd;
        z-index: 999; font-weight: bold;
    }
    th {
        background-color: #E30613 !important; color: white !important;
        font-weight: bold !important; text-transform: uppercase !important;
        text-align: center !important; padding: 12px !important;
    }
    td { text-align: center !important; font-size: 15px !important; }
    
    .kpi-box {
        background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 8px;
        padding: 15px; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .kpi-title { font-size: 14px; color: #555; font-weight: bold; text-transform: uppercase; }
    .kpi-value { font-size: 24px; color: #E30613; font-weight: bold; margin: 5px 0; }
    .kpi-delta { font-size: 15px; font-weight: bold; }
    </style>
    <h1 class="main-title">🔴 MONITOR OPERATIVO FLEXI OCCIDENTE</h1>
    """, unsafe_allow_html=True)

def buscar_archivo(palabra_clave):
    archivos = [f for f in os.listdir('.') if palabra_clave.lower() in f.lower() and f.endswith(('.xlsx', '.csv'))]
    return sorted(archivos)[-1] if archivos else None

archivo_conv = buscar_archivo('Conversion')
archivo_modelos = buscar_archivo('Venta_Modelos')
archivo_comp = buscar_archivo('Comparativo por Operacion')

# --- 1. EL CARTERO LIGERO (COMPARATIVO MENSUAL) ---
def enviar_correo_ejecutivo(tienda_objetivo, conversion, ticket, meta_conv, meta_tkt, faltan_pares, faltan_pesos):
    logro_conv = conversion >= meta_conv
    logro_ticket = ticket >= meta_tkt
    desviacion_conv = conversion - meta_conv
    desviacion_ticket = ticket - meta_tkt

    try:
        remitente = st.secrets["CORREO_REMITENTE"]
        password = st.secrets["CORREO_PASSWORD"]
        destinatario = "fleoutgdl@divec-flexi.com" 
        
        asunto = f"🚀 Desempeño Comercial y Reto Acumulado - Tienda {tienda_objetivo}"
        
        cuerpo = f"Estimada Lety y equipo de la Tienda {tienda_objetivo}:\n\n"
        cuerpo += "Les compartimos el análisis de resultados comerciales de su sucursal, obtenido directamente tras la última actualización del monitor.\n\n"
        cuerpo += "--------------------------------------------------------------------------------\n"
        
        if logro_conv and logro_ticket:
            cuerpo += "🏆 ¡MUCHAS FELICIDADES POR EL RESULTADO!\n"
            cuerpo += "Queremos reconocer el extraordinario desempeño del equipo en el piso de venta. Han alcanzado y superado de forma simultánea las dos metas vitales de nuestra zona para calzado:\n"
            cuerpo += f" * Conversión Actual: {conversion:.2f}% (Meta obligatoria: {meta_conv:.2f}%)\n"
            cuerpo += f" * Ticket Promedio Actual: {ticket:.2f} unidades (Meta obligatoria: {meta_tkt:.2f} unidades de calzado)\n\n"
        else:
            cuerpo += "⚠️ ALERTA DE DESVIACIÓN DE METAS EN PISO DE VENTA\n"
            cuerpo += "Es necesario ajustar la estrategia operativa para alcanzar los objetivos obligatorios de la Zona Occidente:\n"
            if logro_conv:
                cuerpo += f" ✅ CONVERSIÓN: {conversion:.2f}% (Lograda)\n"
            else:
                cuerpo += f" ❌ CONVERSIÓN: {conversion:.2f}% (Faltan {abs(desviacion_conv):.2f}% para alcanzar la meta de {meta_conv}%)\n"
            if logro_ticket:
                cuerpo += f" ✅ TICKET PROMEDIO: {ticket:.2f} unidades (Logrado)\n"
            else:
                cuerpo += f" ❌ TICKET PROMEDIO: {ticket:.2f} unidades (Faltan {abs(desviacion_ticket):.2f} unidades para alcanzar la meta de {meta_tkt})\n\n"
        
        cuerpo += "--------------------------------------------------------------------------------\n"
        cuerpo += "📊 ANÁLISIS COMPARATIVO MENSUAL (RETO ACUMULADO)\n"
        cuerpo += "Para igualar y superar el comparativo histórico del año pasado, al día de hoy el estatus es el siguiente:\n\n"
        
        if faltan_pares > 0:
            cuerpo += f" 👟 Te faltan: {faltan_pares:,.0f} pares de calzado.\n"
        else:
            cuerpo += f" 👟 Llevas a favor: {abs(faltan_pares):,.0f} pares de calzado.\n"
            
        if faltan_pesos > 0:
            cuerpo += f" 💰 Te faltan: ${faltan_pesos:,.2f} MXN en importe.\n\n"
        else:
            cuerpo += f" 💰 Llevas a favor: ${abs(faltan_pesos):,.2f} MXN en importe.\n\n"
        
        cuerpo += "¡Cada cliente que cruza la puerta cuenta para superar esta marca! Éxito en sus ventas.\n"
        cuerpo += "--------------------------------------------------------------------------------\n\n"
        
        cuerpo += "Atentamente,\n"
        cuerpo += "Gerencia Comercial Zona Occidente\n"
        cuerpo += "LAE. José Martín Estrada Cabrera"

        msg = MIMEText(cuerpo)
        msg['Subject'] = asunto
        msg['From'] = remitente
        msg['To'] = destinatario
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(remitente, password)
        server.sendmail(remitente, [destinatario], msg.as_string())
        server.quit()
        return f"✅ Correo ejecutivo enviado exitosamente a la Tienda {tienda_objetivo}."
    except Exception as e:
        return f"❌ Error al enviar el correo a la Tienda {tienda_objetivo}: {e}"

# --- GENERADOR DEL REPORTE TOP 20 EN PDF ---
def generar_reporte_top20_pdf(df_top20, nombre_sucursal):
    hora_mexico = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    fecha_actual = hora_mexico.strftime("%d/%m/%Y")    
    pdf = FPDF(orientation='P', unit='mm', format='Letter')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(227, 6, 19)
    pdf.cell(0, 8, "FLEXI - ZONA OCCIDENTE", ln=True, align="C")
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 8, "AUDITORIA COMERCIAL: TOP 20 MODELOS DE LA SUCURSAL", ln=True, align="C")
    pdf.line(10, 28, 205, 28)
    pdf.ln(8)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(40, 6, "Fecha de Reporte:", 0, 0)
    pdf.cell(60, 6, fecha_actual, 0, 0)
    pdf.cell(35, 6, "Encargada:", 0, 0)
    pdf.cell(60, 6, "_______________________", 0, 1)
    
    pdf.cell(40, 6, "Sucursal:", 0, 0)
    pdf.cell(60, 6, nombre_sucursal, 0, 0)
    pdf.cell(35, 6, "Gerente Comercial:", 0, 0)
    pdf.cell(60, 6, "LAE. Jose Martin Estrada Cabrera", 0, 1)
    pdf.ln(8)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(227, 6, 19)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(15, 8, "#", 1, 0, 'C', fill=True)
    pdf.cell(30, 8, "MODELO", 1, 0, 'C', fill=True)
    pdf.cell(40, 8, "PARES VENDIDOS", 1, 0, 'C', fill=True)
    pdf.cell(110, 8, "DESEMPENO EN LA ZONA OCCIDENTE", 1, 1, 'C', fill=True)
    
    pdf.set_font("Arial", '', 9)
    pdf.set_text_color(0, 0, 0)
    for i, row in df_top20.iterrows():
        posicion = i + 1
        modelo = str(row.get('MODELO', 'S/D'))
        pares = str(row.get('PARES VENDIDOS', '0'))
        if posicion <= 5: desempeno = "Top 5 mas vendido en la region"
        elif posicion <= 10: desempeno = "Alta demanda en la zona"
        else: desempeno = "Desplazamiento regular"
        pdf.cell(15, 7, f"{posicion:02d}", 1, 0, 'C')
        pdf.cell(30, 7, modelo, 1, 0, 'C')
        pdf.cell(40, 7, pares, 1, 0, 'C')
        pdf.cell(110, 7, desempeno, 1, 1, 'L')
        
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, "Nota: Este documento sirve como guia
