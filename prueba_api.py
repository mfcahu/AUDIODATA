import requests
import os
from dotenv import load_dotenv

# Cargar las variables secretas del archivo .env
load_dotenv()

# Extraer la API Key de forma segura
API_KEY = os.getenv("LASTFM_API_KEY")
ARTISTA = "Queen"

# Si por algún motivo no encuentra la clave, avisamos
if not API_KEY:
    print("Error: No se ha encontrado la API Key en el archivo .env")
else:
    url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={ARTISTA}&api_key={API_KEY}&format=json"

    print(f"Conectando con Last.fm para buscar a {ARTISTA} de forma segura...")
    respuesta = requests.get(url)

    if respuesta.status_code == 200:
        datos = respuesta.json()
        oyentes = datos['artist']['stats']['listeners']
        print(f"¡Conexión exitosa! Número de oyentes de {ARTISTA}: {oyentes}")
    else:
        print(f"Error al conectar. Código de error: {respuesta.status_code}")