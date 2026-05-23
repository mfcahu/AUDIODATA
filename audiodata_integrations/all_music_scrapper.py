import cloudscraper
from bs4 import BeautifulSoup
import json
import re
import hashlib
from urllib.parse import quote_plus

BASE_URL = "https://www.allmusic.com"


def _crear_scraper():
    return cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )


def _buscar_url_artista(scraper, nombre_artista):
    url_busqueda = f"{BASE_URL}/search/artists/{quote_plus(nombre_artista)}"
    respuesta = scraper.get(url_busqueda, timeout=15)
    if respuesta.status_code != 200:
        return None

    sopa = BeautifulSoup(respuesta.text, 'html.parser')
    for sel in ['div.name a[href*="/artist/"]', 'a[href*="/artist/mn"]', 'div.artist a[href*="/artist/"]']:
        enlace = sopa.select_one(sel)
        if enlace and enlace.get('href'):
            href = enlace['href']
            return href if href.startswith('http') else BASE_URL + href
    return None


def _extraer_jsonld(sopa):
    for script in sopa.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        candidatos = data if isinstance(data, list) else [data]
        for d in candidatos:
            if isinstance(d, dict) and d.get('@type') in ('MusicGroup', 'Person', 'MusicArtist'):
                return d
    return None


def _extraer_seccion(sopa, etiqueta):
    """
    Extrae el contenido de una sección 'Genre', 'Styles', 'Also Known As'...
    en la ficha de artista de AllMusic.
    """
    # Las páginas modernas usan <div class="genre"> y <div class="styles">, etc.
    # Y también pueden estar como <h4>Genre</h4> seguido de un contenedor.
    nombre_clase = etiqueta.lower().replace(' ', '-')
    
    for sel in [f'div.{nombre_clase}', f'section.{nombre_clase}']:
        div = sopa.select_one(sel)
        if div:
            items = [a.get_text(strip=True) for a in div.find_all('a')]
            items = [i for i in items if i]
            if items:
                return items

    # Por encabezado de texto
    encabezado = sopa.find(['h4', 'h3', 'h2', 'div'], string=re.compile(rf'^\s*{re.escape(etiqueta)}\s*$', re.IGNORECASE))
    if encabezado:
        siguiente = encabezado.find_next_sibling()
        if siguiente:
            items = [a.get_text(strip=True) for a in siguiente.find_all('a')]
            return [i for i in items if i]
    return []


def _datos_estimados(nombre_artista):
    """Datos de respaldo deterministas (RNF.5) solo para descriptores."""
    semilla = int(hashlib.md5(nombre_artista.lower().encode()).hexdigest(), 16)
    pools = [
        ["rock", "classic rock"],
        ["indie", "alternative"],
        ["electronic", "dance"],
        ["pop"],
        ["hip hop"],
        ["jazz"],
        ["folk", "acoustic"],
        ["metal"],
    ]
    return {
        "plataforma": "AllMusic (Mock)",
        "nombre": nombre_artista,
        "descriptores": pools[semilla % len(pools)],
        "es_mock": True,
    }


def extraer_datos_allmusic(nombre_artista):
    """
    Web scraping en AllMusic para obtener géneros y estilos del artista.
    NOTA: AllMusic ya no expone una nota agregada por artista (solo por álbum),
    por lo que esta fuente se usa únicamente para datos cualitativos (descriptores).
    """
    print(f"Buscando '{nombre_artista}' en AllMusic...")

    try:
        scraper = _crear_scraper()
        url_artista = _buscar_url_artista(scraper, nombre_artista)
        if not url_artista:
            print("AllMusic: no se localizó al artista. Usando descriptores estimados (RNF.5).")
            return _datos_estimados(nombre_artista)

        print(f"AllMusic: ficha encontrada en {url_artista}")
        respuesta = scraper.get(url_artista, timeout=15)
        if respuesta.status_code != 200:
            print(f"AllMusic respondió {respuesta.status_code}. Usando descriptores estimados (RNF.5).")
            return _datos_estimados(nombre_artista)

        sopa = BeautifulSoup(respuesta.text, 'html.parser')

        jsonld = _extraer_jsonld(sopa)
        nombre_real = nombre_artista
        generos_jsonld = []
        if jsonld:
            nombre_real = jsonld.get('name', nombre_artista)
            g = jsonld.get('genre', [])
            generos_jsonld = [g] if isinstance(g, str) else list(g)

        generos = _extraer_seccion(sopa, 'Genre') or generos_jsonld
        estilos = _extraer_seccion(sopa, 'Styles')
        descriptores = list(dict.fromkeys(generos + estilos))

        if not descriptores:
            print("AllMusic: ningún descriptor encontrado. Usando datos estimados (RNF.5).")
            return _datos_estimados(nombre_artista)

        print(f"AllMusic: {len(descriptores)} descriptores extraídos: {descriptores}")
        return {
            "plataforma": "AllMusic",
            "nombre": nombre_real,
            "descriptores": descriptores,
            "url": url_artista,
            "es_mock": False,
        }

    except Exception as e:
        print(f"AllMusic: excepción ({e}). Usando descriptores estimados (RNF.5).")
        return _datos_estimados(nombre_artista)


if __name__ == "__main__":
    print(extraer_datos_allmusic("Radiohead"))