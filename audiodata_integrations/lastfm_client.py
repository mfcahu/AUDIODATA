import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://ws.audioscrobbler.com/2.0/"


def obtener_datos_lastfm(nombre_artista):
    """Datos básicos del artista: oyentes y etiquetas."""
    api_key = os.getenv("LASTFM_API_KEY")
    if not api_key:
        print("Error: No se encontró la API Key de Last.fm en el archivo .env")
        return None

    url = f"{BASE_URL}?method=artist.getinfo&artist={nombre_artista}&api_key={api_key}&format=json"
    print(f"Obteniendo datos de '{nombre_artista}' desde Last.fm...")
    respuesta = requests.get(url)

    if respuesta.status_code == 200:
        return respuesta.json()
    print(f"Error al conectar con Last.fm. Código: {respuesta.status_code}")
    return None


def obtener_top_albums_lastfm(nombre_artista, limite=3):
    """
    Top álbumes del artista ordenados por popularidad (playcount).
    Devuelve lista de dicts: nombre, playcount, imagen, url.
    """
    api_key = os.getenv("LASTFM_API_KEY")
    if not api_key:
        return []

    url = (f"{BASE_URL}?method=artist.gettopalbums&artist={nombre_artista}"
           f"&api_key={api_key}&format=json&limit={limite}&autocorrect=1")
    print(f"Obteniendo top {limite} álbumes de '{nombre_artista}' desde Last.fm...")
    try:
        respuesta = requests.get(url, timeout=10)
        if respuesta.status_code != 200:
            return []
        datos = respuesta.json()
        albumes_raw = datos.get('topalbums', {}).get('album', [])
        if not isinstance(albumes_raw, list):
            albumes_raw = [albumes_raw]

        resultado = []
        for a in albumes_raw[:limite]:
            # Filtramos placeholders y "(null)" que devuelve Last.fm
            nombre = a.get('name', '').strip()
            if not nombre or nombre.lower() in ('(null)', 'unknown'):
                continue
            # Imagen: cogemos la de tamaño 'extralarge' o la última disponible
            imagen = ""
            for img in a.get('image', []):
                if isinstance(img, dict) and img.get('#text'):
                    imagen = img['#text']
                    if img.get('size') == 'extralarge':
                        break
            try:
                playcount = int(a.get('playcount', 0))
            except (ValueError, TypeError):
                playcount = 0
            resultado.append({
                "nombre": nombre,
                "playcount": playcount,
                "imagen": imagen,
                "url": a.get('url', '')
            })
        return resultado
    except Exception as e:
        print(f"Last.fm top albums: error {e}")
        return []


if __name__ == "__main__":
    print(obtener_top_albums_lastfm("Radiohead"))