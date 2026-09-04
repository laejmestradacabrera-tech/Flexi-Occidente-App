import feedparser
import pandas as pd
from datetime import datetime

def recolectar_noticias():
    print("Iniciando fase 2: Agente de Inteligencia (Filtro Robusto Calzado y Macro)...")
    
    # Fuentes estratégicas
    fuentes = {
        "Mercado de Calzado (Global)": "https://wwd.com/footwear-news/feed/",
        "Piso de Ventas y Retail": "https://www.retaildive.com/feeds/news/",
        "Logística y Suministro": "https://www.supplychaindive.com/feeds/news/",
        "Entorno Económico México": "https://www.forbes.com.mx/feed/"
    }
    
    # Filtro Inteligente: Palabras en minúsculas (MÁS ESTRICTO)
    palabras_clave = [
        "shoe", "footwear", "calzado", "sneaker", "zapatos", "botas", "zapatería", 
        "leather", "piel", "suela", "apparel",
        "inflation", "inflación", "supply chain", "interest rates", "tasas de interés"
    ]
    
    # LISTA NEGRA: Si la noticia tiene esto, se va a la basura automáticamente
    # Lululemon NO está aquí porque sí es competencia en lifestyle/calzado
    palabras_basura = [
        "makeup", "beauty", "cosmetics", "maquillaje", "belleza", "grocery", 
        "supermarket", "food", "comida", "ulta", "dollar general", 
        "target", "walmart", "beverage", "skincare", "kroger"
    ]
    
    datos = []
    
    for categoria, url in fuentes.items():
        try:
            feed = feedparser.parse(url)
            articulos_agregados = 0
            
            for entry in feed.entries:
                # Extracción robusta de texto
                texto_analizar = entry.title.lower()
                if hasattr(entry, 'summary'):
                    texto_analizar += " " + entry.summary.lower()
                elif hasattr(entry, 'description'):
                    texto_analizar += " " + entry.description.lower()
                
                # LA NUEVA PRUEBA DE FUEGO: Tiene que tener palabras clave Y NO tener palabras basura
                if any(palabra in texto_analizar for palabra in palabras_clave) and not any(basura in texto_analizar for basura in palabras_basura):
                    fecha_pub = entry.published if hasattr(entry, 'published') else "Reciente"
                    
                    datos.append({
                        "Categoría": categoria,
                        "Título": entry.title,
                        "Fecha": fecha_pub,
                        "Enlace": entry.link,
                        "Última Actualización": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    articulos_agregados += 1
                    
                # Límite de las 5 más relevantes
                if articulos_agregados >= 5:
                    break
        except Exception as e:
            print(f"Error leyendo la fuente {categoria}: {e}")
            
    # Guardado y actualización forzada
    # Si 'datos' está vacío, creamos un DataFrame vacío con las columnas correctas
    if not datos:
        df = pd.DataFrame(columns=["Categoría", "Título", "Fecha", "Enlace", "Última Actualización"])
        print("⚠️ No se encontraron artículos relevantes hoy. Limpiando tabla.")
    else:
        df = pd.DataFrame(datos)
        print(f"✅ Extracción inteligente exitosa. {len(df)} artículos filtrados guardados.")

    nombre_archivo = "datos_inteligencia.csv"
    df.to_csv(nombre_archivo, index=False)

if __name__ == "__main__":
    recolectar_noticias()
