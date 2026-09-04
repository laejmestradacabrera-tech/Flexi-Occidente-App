import feedparser
import pandas as pd
from datetime import datetime

def recolectar_noticias():
    print("Iniciando fase 2: Agente de Inteligencia (Filtro Robusto Calzado y Macro)...")
    
    # Fuentes estratégicas
    fuentes = {
        "Mercado de Calzado (Global)": "https://footwearnews.com/feed/",
        "Piso de Ventas y Retail": "https://www.retaildive.com/feeds/news/",
        "Economía y Consumidor (MX)": "https://www.forbes.com.mx/category/negocios/feed/",
        "Logística y Suministro": "https://www.supplychaindive.com/feeds/news/"
    }
    
    # Filtro Inteligente: Palabras en minúsculas
    palabras_clave = [
        "shoe", "footwear", "calzado", "sneaker", "zapatos", "retail", 
        "store", "tienda", "consumer", "consumidor", "inflation", 
        "inflación", "supply", "logística", "inventario", "inventory",
        "ventas", "sales", "economy", "economía", "precio", "tasas"
    ]
    
    datos = []
    
    for categoria, url in fuentes.items():
        try:
            feed = feedparser.parse(url)
            articulos_agregados = 0
            
            for entry in feed.entries:
                # Extracción robusta de texto: Buscamos en título, resumen y descripción si existen
                texto_analizar = entry.title.lower()
                if hasattr(entry, 'summary'):
                    texto_analizar += " " + entry.summary.lower()
                elif hasattr(entry, 'description'):
                    texto_analizar += " " + entry.description.lower()
                
                # Verificamos si alguna palabra clave está en todo el texto escaneado
                if any(palabra in texto_analizar for palabra in palabras_clave):
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
