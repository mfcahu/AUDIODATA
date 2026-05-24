import cloudscraper
from bs4 import BeautifulSoup
import re
import hashlib
import math
import time
from urllib.parse import quote_plus

BASE_URL = "https://www.besteveralbums.com"


def _crear_scraper():
    return cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )


def _buscar_url_via_bing(scraper, nombre_artista):
    """
    Búsqueda principal usando Bing. Más fiable que DuckDuckGo
    (que devuelve 202 cuando detecta scraping).
    """
    try:
        query = quote_plus(f"site:besteveralbums.com {nombre_artista} artist")
        url_bing = f"https://www.bing.com/search?q={query}"
        respuesta = scraper.get(url_bing, timeout=15)
        if respuesta.status_code != 200:
            return None
        sopa = BeautifulSoup(respuesta.text, 'html.parser')

        # Buscar URLs de BEA en los resultados
        for enlace in sopa.find_all('a', href=True):
            href = enlace['href']
            match = re.search(r'(https?://(?:www\.)?besteveralbums\.com/thechart\.php\?b=\d+)', href)
            if match:
                return match.group(1)
        return None
    except Exception:
        return None


def _buscar_url_interna(scraper, nombre_artista):
    """Fallback: buscador interno de BEA."""
    nombre_para_url = quote_plus(nombre_artista)
    urls_busqueda = [
        f"{BASE_URL}/searchresults.php?searchterm={nombre_para_url}&searchtype=Bands",
        f"{BASE_URL}/searchresults.php?q={nombre_para_url}&searchtype=Bands",
    ]
    for url_busqueda in urls_busqueda:
        try:
            respuesta = scraper.get(url_busqueda, timeout=15)
            if respuesta.status_code != 200:
                continue
            sopa = BeautifulSoup(respuesta.text, 'html.parser')
            primer = sopa.find('a', href=re.compile(r'/thechart\.php\?b=\d+'))
            if primer:
                href = primer['href']
                return href if href.startswith('http') else BASE_URL + '/' + href.lstrip('/')
        except Exception:
            continue
    return None


def _buscar_url_artista(scraper, nombre_artista):
    # 1) Bing primero (más fiable)
    url = _buscar_url_via_bing(scraper, nombre_artista)
    if url:
        return url
    # 2) Fallback al buscador interno de BEA
    return _buscar_url_interna(scraper, nombre_artista)


def _extraer_average_rating(texto):
    match = re.search(r'Average Rating[^\d]*([\d\.]+)\s*/\s*100\s*\(from\s*([\d,]+)\s*votes?\)', texto, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1)), int(match.group(2).replace(',', ''))
        except ValueError:
            pass
    match = re.search(r'Average Rating[^\d]*([\d\.]+)\s*/\s*100', texto, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1)), None
        except ValueError:
            pass
    return None, None


def _extraer_stats_globales(texto):
    num_charts = None
    match = re.search(r'appears? in ([\d,]+) charts?', texto, re.IGNORECASE)
    if match:
        try:
            num_charts = int(match.group(1).replace(',', ''))
        except ValueError:
            pass
    num_ratings_globales = None
    match = re.search(r'([\d,]+) ratings? from BestEverAlbums', texto, re.IGNORECASE)
    if match:
        try:
            num_ratings_globales = int(match.group(1).replace(',', ''))
        except ValueError:
            pass
    pais = None
    match_pais = re.search(r'from ([A-Z][A-Za-z ]+?)\.\s', texto)
    if match_pais:
        pais = match_pais.group(1).strip()
    return num_charts, num_ratings_globales, pais


def _extraer_top_albums(sopa, limite=3):
    """
    Recoge enlaces /thechart.php?a=ID pero filtrando los que NO son nombre de álbum
    (los que son '4,460 charts' o '92 (5,673 votes)', que son enlaces a anclas).
    Solo aceptamos el primer enlace por ID (los demás son repetidos del mismo álbum).
    """
    resultado = []
    ids_vistos = set()

    for enlace in sopa.find_all('a', href=re.compile(r'/thechart\.php\?a=(\d+)')):
        if len(resultado) >= limite:
            break

        href = enlace['href']
        nombre = enlace.get_text(strip=True)

        # ID del álbum
        match_id = re.search(r'a=(\d+)', href)
        if not match_id:
            continue
        album_id = match_id.group(1)
        if album_id in ids_vistos:
            continue

        # Filtros: el enlace tiene que ser el nombre del álbum,
        # no un texto como "4,460 charts" o "92 (5,673 votes)"
        if not nombre or len(nombre) < 2:
            continue
        if re.match(r'^\d', nombre):  # empieza con dígito (es una estadística)
            continue
        if 'votes' in nombre.lower() or 'charts' in nombre.lower() or 'rating' in nombre.lower():
            continue
        if '#' in href:  # enlaces con fragmento (#rankings, #ratings) son a estadísticas
            continue

        ids_vistos.add(album_id)

        url_album = href if href.startswith('http') else BASE_URL + '/' + href.lstrip('/')

        year = None
        padre = enlace.find_parent(['tr', 'div', 'li', 'p'])
        if padre:
            m = re.search(r'\b(19[3-9]\d|20\d{2})\b', padre.get_text(' ', strip=True))
            if m:
                year = int(m.group(1))

        imagen = ""
        img_tag = padre.find('img') if padre else None
        if img_tag:
            imagen = img_tag.get('data-src') or img_tag.get('src', '')
            if imagen and not imagen.startswith('http'):
                imagen = BASE_URL + '/' + imagen.lstrip('/')

        resultado.append({"nombre": nombre, "year": year, "imagen": imagen, "url": url_album})

    return resultado


def _datos_estimados(nombre_artista):
    semilla = int(hashlib.md5(nombre_artista.lower().encode()).hexdigest(), 16)
    return {
        "plataforma": "BestEverAlbums (Mock)",
        "nombre": nombre_artista,
        "num_charts": 50 + (semilla % 5000),
        "num_ratings": 10 + (semilla % 500),
        "pais": None,
        "nota_normalizada": round(40 + (semilla % 6000) / 100, 1),
        "top_albums": [],
        "es_mock": True,
    }


def extraer_datos_besteveralbums(nombre_artista):
    print(f"Buscando '{nombre_artista}' en BestEverAlbums...")
    try:
        scraper = _crear_scraper()
        url_artista = _buscar_url_artista(scraper, nombre_artista)
        if not url_artista:
            print("BEA: no se localizó al artista. Usando datos estimados (RNF.5).")
            return _datos_estimados(nombre_artista)

        print(f"BEA: ficha encontrada en {url_artista}")
        time.sleep(0.5)
        respuesta = scraper.get(url_artista, timeout=15)
        if respuesta.status_code != 200:
            print(f"BEA respondió {respuesta.status_code}. Usando datos estimados (RNF.5).")
            return _datos_estimados(nombre_artista)

        sopa = BeautifulSoup(respuesta.text, 'html.parser')
        texto = re.sub(r'\s+', ' ', sopa.get_text(' ', strip=True))

        nota_real, num_votos = _extraer_average_rating(texto)
        num_charts, num_ratings_globales, pais = _extraer_stats_globales(texto)
        top_albums = _extraer_top_albums(sopa)

        if nota_real is None and num_charts is None and num_ratings_globales is None and not top_albums:
            print("BEA: HTML no parseable. Usando datos estimados (RNF.5).")
            return _datos_estimados(nombre_artista)

        if nota_real is not None:
            nota_normalizada = round(float(nota_real), 1)
            num_ratings_usar = num_votos if num_votos is not None else (num_ratings_globales or 0)
            print(f"BEA: Average Rating = {nota_real}/100 ({num_ratings_usar} votos), charts={num_charts}, álbumes={len(top_albums)}")
        else:
            num_ratings_usar = num_ratings_globales or 0
            if num_charts and num_charts > 0:
                nota_normalizada = round(min(100.0, (math.log10(num_charts) / 4.0) * 100), 1)
            else:
                nota_normalizada = 0.0
            print(f"BEA: nota derivada de charts={num_charts} -> {nota_normalizada}, álbumes={len(top_albums)}")

        return {
            "plataforma": "BestEverAlbums",
            "nombre": nombre_artista,
            "num_charts": num_charts or 0,
            "num_ratings": num_ratings_usar,
            "pais": pais,
            "nota_normalizada": nota_normalizada,
            "top_albums": top_albums,
            "url": url_artista,
            "es_mock": False,
        }

    except Exception as e:
        print(f"BEA: excepción ({e}). Usando datos estimados (RNF.5).")
        return _datos_estimados(nombre_artista)


if __name__ == "__main__":
    print(extraer_datos_besteveralbums("Radiohead"))