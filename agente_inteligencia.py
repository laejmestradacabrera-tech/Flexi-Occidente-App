import feedparser
import pandas as pd
from datetime import datetime

try:
    from googletrans import Translator
except ImportError:
    print("⚠️ Advertencia: Librería googletrans no instalada. La traducción automática estará desactivada.")
    Translator = None

def recolectar_noticias():
    print("Iniciando fase avanzada: Agente de Inteligencia (Calzado, Malls, INEGI y Macroeconomía)...")

    # 1. Configuración del Traductor
    traductor = Translator() if Translator else None

    # 2. Fuentes estratégicas diferenciadas por naturaleza
    fuentes_calzado_retail = {
        "Mercado de Calzado (Global)": "https://wwd.com/footwear-news/feed/",
        "Piso de Ventas y Retail": "https://www.retaildive.com/feeds/news/",
        "Logística y Suministro": "https://www.supplychaindive.com/feeds/news/"
    }

    fuentes_macro_mexico = {
        "Macroeconomía y Consumo México": "https://www.eleconomista.com.mx/rss/empresas/",
        "Indicadores Oficiales (INEGI)": "https://www.inegi.org.mx/rss/noticias.xml"
    }

    # 3. Filtros específicos y separados
    palabras_clave_retail = [
        "shoe", "footwear", "calzado", "sneaker", "zapatos", "botas", "zapatería", "piel", "suela", 
        "supply chain", "retail", "ventas", "mall", "centro comercial", "plaza", "desarrollo", "apertura", "expansion"
    ]

    palabras_clave_macro = [
        "inflación", "inflation", "pib", "consumidor", "consumo", "tasas", "interés", 
        "economía", "empleo", "ventas", "comercio", "inegi", "precio", "banco de méxico", "banxico"
    ]

    palabras_basura = [
        "makeup", "beauty", "cosmetics", "maquillaje", "belleza", "grocery", 
        "supermarket", "food", "comida", "ulta", "dollar general", 
        "target", "walmart", "beverage", "skincare", "kroger", "farmacia", "cvs", "walgreens"
    ]

    datos = []

    # --- PROCESAMIENTO FUENTES DE CALZADO Y RETAIL ---
    for categoria, url in fuentes_calzado_retail.items():
        try:
            print(f"📡 Leyendo fuente especializada: {categoria}...")
            feed = feedparser.parse(url)
            articulos_agregados = 0
            
            for entry in feed.entries:
                titulo_original = entry.title
                texto_busqueda = titulo_original.lower()
                if hasattr(entry, 'summary'):
                    texto_busqueda += " " + entry.summary.lower()
                elif hasattr(entry, 'description'):
                    texto_busqueda += " " + entry.description.lower()
                
                tiene_clave = any(palabra in texto_busqueda for palabra in palabras_clave_retail)
                tiene_basura = any(basura in texto_busqueda for basura in palabras_basura)
                
                if tiene_clave and not tiene_basura:
                    titulo_final = titulo_original
                    if traductor:
                        try:
                            deteccion = traductor.detect(titulo_original)
                            if deteccion.lang == 'en':
                                traduccion = traductor.translate(titulo_original, dest='es')
                                titulo_final = f"{traduccion.text} (En)"
                        except:
                            titulo_final = titulo_original
                    
                    fecha_pub = entry.published if hasattr(entry, 'published') else "Reciente"
                    datos.append({
                        "Categoría": categoria,
                        "Título": titulo_final,
                        "Fecha": fecha_pub,
                        "Enlace": entry.link,
                        "Última Actualización": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    articulos_agregados += 1
                if articulos_agregados >= 5: break
        except Exception as e:
            print(f"❌ Error leyendo fuente {categoria}: {e}")

    # --- PROCESAMIENTO FUENTES MACRO Y OFICIALES (INEGI / MÉXICO) ---
    for categoria, url in fuentes_macro_mexico.items():
        try:
            print(f"📡 Leyendo fuente oficial/macro: {categoria}...")
            feed = feedparser.parse(url)
            articulos_agregados = 0
            
            for entry in feed.entries:
                titulo_original = entry.title
                texto_busqueda = titulo_original.lower()
                if hasattr(entry, 'summary'):
                    texto_busqueda += " " + entry.summary.lower()
                elif hasattr(entry, 'description'):
                    texto_busqueda += " " + entry.description.lower()
                
                es_del_inegi = "INEGI" in categoria
                tiene_macro = any(m in texto_busqueda for m in palabras_clave_macro)
                
                # Para fuentes macro e INEGI permitimos el pase directo si tocan temas económicos oficiales
                if es_del_inegi or tiene_macro:
                    fecha_pub = entry.published if hasattr(entry, 'published') else "Reciente"
                    datos.append({
                        "Categoría": categoria,
                        "Título": titulo_original,
                        "Fecha": fecha_pub,
                        "Enlace": entry.link,
                        "Última Actualización": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    articulos_agregados += 1
                if articulos_agregados >= 4: break
        except Exception as e:
            print(f"❌ Error leyendo fuente macro {categoria}: {e}")
            
    # 6. Guardado final de resultados
    if not datos:
        df = pd.DataFrame(columns=["Categoría", "Título", "Fecha", "Enlace", "Última Actualización"])
        print("⚠️ No se encontraron artículos bajo los filtros actuales.")
    else:
        df = pd.DataFrame(datos)
        print(f"✅ ¡Extracción exitosa! {len(df)} artículos recolectados.")

    df.to_csv("datos_inteligencia.csv", index=False)

if __name__ == "__main__":
    recolectar_noticias()
