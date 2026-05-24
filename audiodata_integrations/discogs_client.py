import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.discogs.com"
HEADERS_BASE = {"User-Agent": "AudiodataProject/1.0"}


def obtener_datos_discogs(nombre_artista):
    """Datos básicos del artista: id e imagen."""
    token = os.getenv("DISCOGS_TOKEN")
    if not token:
        return None

    url = f"{API_BASE}/database/search?q={nombre_artista}&type=artist&token={token}"
    print(f"Buscando a '{nombre_artista}' en Discogs...")
    respuesta = requests.get(url, headers=HEADERS_BASE)

    if respuesta.status_code == 200:
        datos = respuesta.json()
        if datos.get('results'):
            primer_resultado = datos['results'][0]
            return {
                "plataforma": "Discogs",
                "id_discogs": primer_resultado.get("id"),
                "titulo": primer_resultado.get("title"),
                "imagen": primer_resultado.get("cover_image")
            }
    return None


def _normalizar_titulo_album(titulo):
    """
    Normaliza el título para deduplicar variantes:
    'OK Computer (Deluxe Edition)' -> 'ok computer'
    'OK Computer [Remastered]' -> 'ok computer'
    """
    if not titulo:
        return ""
    # Quitar contenido entre paréntesis o corchetes
    t = re.sub(r'\s*[\(\[].*?[\)\]]', '', titulo)
    # Quitar sufijos comunes
    t = re.sub(r'\s*-\s*(deluxe|remaster.*|special edition|anniversary.*)$', '', t, flags=re.IGNORECASE)
    return t.strip().lower()


def obtener_top_albums_discogs(nombre_artista, limite=3):
    """
    Top álbumes por demanda de coleccionistas (campo 'have' en Discogs).
    Devuelve lista de dicts: nombre, have, want, year, imagen.
    """
    token = os.getenv("DISCOGS_TOKEN")
    if not token:
        return []

    # Buscamos releases con formato álbum, ordenados por demanda
    url = (f"{API_BASE}/database/search?artist={nombre_artista}"
           f"&type=release&format=album&per_page=50&token={token}")
    print(f"Obteniendo top {limite} álbumes de '{nombre_artista}' desde Discogs...")
    try:
        respuesta = requests.get(url, headers=HEADERS_BASE, timeout=15)
        if respuesta.status_code != 200:
            return []

        resultados = respuesta.json().get('results', [])

        # Deduplicar por título normalizado, quedándonos con el de mayor 'have'
        mejor_por_titulo = {}
        for r in resultados:
            titulo_raw = r.get('title', '')
            # En búsquedas de Discogs el título suele ser "Artista - Álbum"
            partes = titulo_raw.split(' - ', 1)
            titulo_album = partes[1] if len(partes) == 2 else titulo_raw

            clave = _normalizar_titulo_album(titulo_album)
            if not clave:
                continue

            community = r.get('community', {}) or {}
            have = community.get('have', 0) or 0
            want = community.get('want', 0) or 0
            year = r.get('year')
            imagen = r.get('cover_image', '')

            if clave not in mejor_por_titulo or have > mejor_por_titulo[clave]['have']:
                mejor_por_titulo[clave] = {
                    "nombre": titulo_album.strip(),
                    "have": have,
                    "want": want,
                    "year": year,
                    "imagen": imagen,
                }

        # Ordenamos por 'have' descendente y cogemos los N primeros
        top = sorted(mejor_por_titulo.values(), key=lambda x: x['have'], reverse=True)
        return top[:limite]

    except Exception as e:
        print(f"Discogs top albums: error {e}")
        return []


if __name__ == "__main__":
    print(obtener_top_albums_discogs("Daft Punk"))