import requests
import os
from dotenv import load_dotenv

load_dotenv()

def obtener_datos_discogs(nombre_artista):
    token = os.getenv("DISCOGS_TOKEN")
    if not token:
        return None
        
    url = f"https://api.discogs.com/database/search?q={nombre_artista}&type=artist&token={token}"
    headers = {"User-Agent": "AudiodataProject/1.0"}
    
    print(f"Buscando a '{nombre_artista}' en Discogs...")
    respuesta = requests.get(url, headers=headers)
    
    if respuesta.status_code == 200:
        datos = respuesta.json()
        if datos.get('results'):
            primer_resultado = datos['results'][0]
            return {
                "plataforma": "Discogs",
                "id_discogs": primer_resultado.get("id"),
                "titulo": primer_resultado.get("title"),
                "imagen": primer_resultado.get("cover_image") # ¡NUEVO: Atrapamos la imagen!
            }
    return None

if __name__ == "__main__":
    print(obtener_datos_discogs("Queen"))