import feedparser
import pandas as pd
from datetime import datetime
try:
    from googletrans import Translator
except ImportError:
    print("⚠️ Advertencia: Librería googletrans no instalada. La traducción automática estará desactivada.")
    Translator = None

def recolectar_noticias():
    print("Iniciando fase 3: Agente de Inteligencia (INEGI, Malls, Calzado y Traducción)...")
    
    # 1. Configuración del Traductor
    traductor = Translator() if Translator else None

    # 2. Fuentes estratégicas enriquecidas
    fuentes = {
        "Mercado de Calzado (Global)": "https://wwd.com/footwear-news/feed/",
        "Piso de Ventas y Retail": "https://www.retaildive.com/feeds/news/",
        "Logística y Suministro": "https://www.supplychaindive.com/feeds/news/",
        "Macroeconomía México": "https://www.eleconomista.com.mx/rss/empresas/",
        "Indicadores Oficiales (INEGI)": "https://www.inegi.org.mx/rss/noticias.xml" # Fuente oficial añadida
    }
    
    # 3. Filtro Inteligente: Palabras en minúsculas (MÁS ESTRICTO Y ENFOCADO)
    palabras_clave = [
        "shoe", "footwear", "calzado", "sneaker", "zapatos", "botas", "zapatería", "piel", "suela", 
        "inflation", "inflación", "supply chain", "interest rates", "tasas de interés", "consumidor",
        "consumo", "inegi", "pib", "retail", "ventas",
        "mall", "centro comercial", "plaza", "desarrollo", "apertura", "expansion" # Rastreando nuevos malls
    ]
    
    # 4. LISTA NEGRA: Basura, cosméticos, supermercados, comida (Sacamos a Lululemon de aquí)
    palabras_basura = [
        "makeup", "beauty", "cosmetics", "maquillaje", "belleza", "grocery", 
        "supermarket", "food", "comida", "ulta", "dollar general", 
        "target", "walmart", "beverage", "skincare", "kroger", "farmacia", "cvs", "walgreens"
    ]
    
    datos = []
    
    for categoria, url in fuentes.items():
        try:
            print(f"📡 Leyendo fuente: {categoria}...")
            feed = feedparser.parse(url)
            articulos_agregados = 0
            
            for entry in feed.entries:
                titulo_original = entry.title
                
                # Extracción robusta de texto de búsqueda
                texto_busqueda = titulo_original.lower()
                if hasattr(entry, 'summary'):
                    texto_busqueda += " " + entry.summary.lower()
                elif hasattr(entry, 'description'):
                    texto_busqueda += " " + entry.description.lower()
                
                # LA PRUEBA DE FUEGO: Tiene palabras clave Y NO tiene palabras basura
                tiene_clave = any(palabra in texto_busqueda for palabra in palabras_clave)
                tiene_basura = any(basura in texto_busqueda for basura in palabras_basura)
                
                # Si es del INEGI, la pasamos directo asumiendo que es relevante (macroeconomía)
                if (tiene_clave and not tiene_basura) or "INEGI" in categoria:
                    
                    titulo_final = titulo_original
                    
                    # 5. Módulo de Traducción Automática (Solo para fuentes en inglés)
                    if traductor and ("Global" in categoria or "Retail" in categoria or "Logística" in categoria):
                        try:
                            # Detectamos el idioma, si es 'en', traducimos a 'es'
                            deteccion = traductor.detect(titulo_original)
                            if deteccion.lang == 'en':
                                traduccion = traductor.translate(titulo_original, dest='es')
                                titulo_final = f"{traduccion.text} (En)"
                        except Exception as e:
                            print(f"  - Error menor traduciendo: {titulo_original[:20]}... : {e}")
                            titulo_final = titulo_original # Si falla la traducción, dejamos el original
                    
                    fecha_pub = entry.published if hasattr(entry, 'published') else "Reciente"
                    
                    datos.append({
                        "Categoría": categoria,
                        "Título": titulo_final,
                        "Fecha": fecha_pub,
                        "Enlace": entry.link,
                        "Última Actualización": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    articulos_agregados += 1
                    
                # Límite para no saturar la tabla (traemos las 6 más frescas por fuente)
                if articulos_agregados >= 6:
                    break
                    
        except Exception as e:
            print(f"❌ Error crítico leyendo la fuente {categoria}: {e}")
            
    # 6. Guardado y actualización forzada
    if not datos:
        df = pd.DataFrame(columns=["Categoría", "Título", "Fecha", "Enlace", "Última Actualización"])
        print("⚠️ No se encontraron artículos relevantes bajo el nuevo filtro. Tabla limpia.")
    else:
        df = pd.DataFrame(datos)
        print(f"✅ ¡Extracción e Inteligencia exitosa! {len(df)} artículos guardados (Macro + Malls + Calzado).")

    nombre_archivo = "datos_inteligencia.csv"
    df.to_csv(nombre_archivo, index=False)

if __name__ == "__main__":
    recolectar_noticias()
