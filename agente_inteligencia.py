import feedparser
import pandas as pd
from datetime import datetime

def recolectar_noticias():
    print("Iniciando fase 2: Agente de Inteligencia (Filtro Calzado y Macro)...")
    
    # 1. Fuentes estratégicas: Calzado, Retail General, Logística y Macroeconomía (MX/Latam)
    fuentes = {
        "Mercado de Calzado (Global)": "https://footwearnews.com/feed/",
        "Piso de Ventas y Retail": "https://www.retaildive.com/feeds/news/",
        "Economía y Consumidor (MX)": "https://www.forbes.com.mx/category/negocios/feed/",
        "Logística y Suministro": "https://www.supplychaindive.com/feeds/news/"
    }
    
    # 2. El Filtro Inteligente: Solo pasará información que contenga estos temas vitales
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
                # Unimos título y descripción para escanear de qué trata la noticia
                texto_analizar = (entry.title + " " + getattr(entry, 'description', '')).lower()
                
                # 3. Verificamos si alguna palabra clave está en el texto de la noticia
                if any(palabra in texto_analizar for palabra in palabras_clave):
                    # Formateo de fecha por si la fuente no la provee
                    fecha_pub = entry.published if hasattr(entry, 'published') else "Reciente"
                    
                    datos.append({
                        "Categoría": categoria,
                        "Título": entry.title,
                        "Fecha": fecha_pub,
                        "Enlace": entry.link,
                        "Última Actualización": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    articulos_agregados += 1
                    
                # Limitamos a los 5 artículos MÁS RELEVANTES por categoría para no saturar tu lectura
                if articulos_agregados >= 5:
                    break
        except Exception as e:
            print(f"Error leyendo la fuente {categoria}: {e}")
            
    # 4. Guardado y actualización
    if datos:
        df = pd.DataFrame(datos)
        nombre_archivo = "datos_inteligencia.csv"
        df.to_csv(nombre_archivo, index=False)
        print(f"✅ Extracción inteligente exitosa. {len(df)} artículos filtrados guardados.")
    else:
        print("⚠️ No se encontraron artículos relevantes bajo los criterios de hoy.")

if __name__ == "__main__":
    recolectar_noticias()
