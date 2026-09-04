import feedparser
import pandas as pd
from datetime import datetime
import os

def recolectar_noticias():
    print("Iniciando el Agente de Inteligencia Comercial...")
    
    # Fuentes RSS públicas y gratuitas enfocadas en Retail, Suministro y Moda
    fuentes = {
        "Piso de Ventas y Retail": "https://www.retaildive.com/feeds/news/",
        "Logística y Suministro": "https://www.supplychaindive.com/feeds/news/"
    }
    
    datos = []
    
    for categoria, url in fuentes.items():
        print(f"Consultando: {categoria}...")
        try:
            feed = feedparser.parse(url)
            # Extraemos los 5 artículos más recientes de cada fuente
            for entry in feed.entries[:5]:
                datos.append({
                    "Categoría": categoria,
                    "Título": entry.title,
                    "Fecha": entry.published,
                    "Enlace": entry.link,
                    "Última Actualización": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
        except Exception as e:
            print(f"Error al consultar {categoria}: {e}")
            
    if datos:
        df = pd.DataFrame(datos)
        
        # Guardamos la tabla en un archivo CSV en la misma carpeta
        nombre_archivo = "datos_inteligencia.csv"
        df.to_csv(nombre_archivo, index=False)
        print(f"✅ Éxito: Archivo '{nombre_archivo}' generado con {len(df)} registros.")
    else:
        print("⚠️ No se encontraron datos en esta ejecución.")

if __name__ == "__main__":
    recolectar_noticias()
