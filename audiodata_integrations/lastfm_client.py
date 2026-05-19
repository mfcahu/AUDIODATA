import requests
import os
from dotenv import load_dotenv

# Cargamos las variables secretas al iniciar este módulo
load_dotenv()

def obtener_datos_lastfm(nombre_artista):
    """
    Se conecta a la API de Last.fm y devuelve los datos en bruto del artista solicitado.
    """
    api_key = os.getenv("LASTFM_API_KEY")
    
    if not api_key:
        print("Error: No se encontró la API Key de Last.fm en el archivo .env")
        return None

    # Insertamos el nombre del artista dinámicamente en la URL
    url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={nombre_artista}&api_key={api_key}&format=json"
    
    print(f"Obteniendo datos de '{nombre_artista}' desde Last.fm...")
    respuesta = requests.get(url)
    
    # Verificamos que la petición fue un éxito
    if respuesta.status_code == 200:
        return respuesta.json()
    else:
        print(f"Error al conectar con Last.fm. Código: {respuesta.status_code}")
        return None

# Este bloque solo se ejecuta si probamos este archivo directamente
if __name__ == "__main__":
    datos = obtener_datos_lastfm("Queen")
    if datos:
        oyentes = datos['artist']['stats']['listeners']
        print(f"¡Prueba de arquitectura exitosa! Oyentes de Queen: {oyentes}")