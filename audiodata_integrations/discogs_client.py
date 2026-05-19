import requests
import os
from dotenv import load_dotenv

load_dotenv()

def obtener_datos_discogs(nombre_artista):
    """
    Se conectará a la API de Discogs para buscar al artista y obtener su ID oficial.
    """
    token = os.getenv("DISCOGS_TOKEN")
    
    if not token:
        print("Error: No se encontró DISCOGS_TOKEN en el archivo .env")
        return None
        
    # URL oficial de Discogs para buscar artistas
    url = f"https://api.discogs.com/database/search?q={nombre_artista}&type=artist&token={token}"
    
    # Discogs exige que nos identifiquemos con un nombre de aplicación personalizado
    headers = {
        "User-Agent": "AudiodataProject/1.0"
    }
    
    print(f"Buscando a '{nombre_artista}' en la base de datos de Discogs...")
    respuesta = requests.get(url, headers=headers)
    
    if respuesta.status_code == 200:
        datos = respuesta.json()
        
        # Comprobamos si la lista de resultados no está vacía
        if datos.get('results'):
            primer_resultado = datos['results'][0]
            # Devolvemos la información útil que encontremos
            return {
                "plataforma": "Discogs",
                "id_discogs": primer_resultado.get("id"),
                "titulo": primer_resultado.get("title")
            }
        else:
            print("No se encontraron resultados en Discogs.")
            return None
    else:
        print(f"Error al conectar con Discogs. Código: {respuesta.status_code}")
        return None

# Bloque de prueba local
if __name__ == "__main__":
    resultado = obtener_datos_discogs("Queen")
    if resultado:
        print("¡Éxito! Datos obtenidos de Discogs:")
        print(resultado)