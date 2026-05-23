import cloudscraper
from bs4 import BeautifulSoup
import re
import hashlib
import math
from urllib.parse import quote_plus

BASE_URL = "https://www.besteveralbums.com"


def _crear_scraper():
    return cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )


def _buscar_url_artista(scraper, nombre_artista):
    """
    Estrategias en cascada para localizar la ficha del artista en BEA:
      1) Búsqueda interna de BEA con diferentes nombres de parámetro.
      2) Búsqueda con DuckDuckGo (rápido, sin captchas) usando site:besteveralbums.com.
    """
    nombre_para_url = quote_plus(nombre_artista)
    nombre_para_path = nombre_artista.lower().replace(' ', '-')

    # Estrategia 1: probar todas las variantes razonables del buscador interno
    urls_busqueda = [
        f"{BASE_URL}/searchresults.php?searchterm={nombre_para_url}&searchtype=Bands",
        f"{BASE_URL}/searchresults.php?q={nombre_para_url}&searchtype=Bands",
        f"{BASE_URL}/searchresults.php?searchterm={nombre_para_url}&searchtype=2",
        f"{BASE_URL}/searchresults.php?searchterm={nombre_para_url}",
        f"{BASE_URL}/search.php?q={nombre_para_url}",
    ]
    for url_busqueda in urls_busqueda:
        try:
            respuesta = scraper.get(url_busqueda, timeout=15)
            if respuesta.status_code != 200:
                continue
            sopa = BeautifulSoup(respuesta.text, 'html.parser')
            # En la página de resultados, las fichas de artista son enlaces tipo /thechart.php?b=ID
            for enlace in sopa.find_all('a', href=re.compile(r'/thechart\.php\?b=\d+')):
                href = enlace.get('href', '')
                texto_enlace = enlace.get_text(strip=True).lower()
                # Solo aceptamos si el texto del enlace contiene el nombre buscado
                if nombre_artista.lower() in texto_enlace or texto_enlace in nombre_artista.lower():
                    return href if href.startswith('http') else BASE_URL + '/' + href.lstrip('/')
            # Si no hay coincidencia exacta, tomamos el primer enlace de artista de la página
            primer_enlace = sopa.find('a', href=re.compile(r'/thechart\.php\?b=\d+'))
            if primer_enlace:
                href = primer_enlace['href']
                return href if href.startswith('http') else BASE_URL + '/' + href.lstrip('/')
        except Exception:
            continue

    # Estrategia 2: fallback con DuckDuckGo (sin API, devuelve HTML simple)
    try:
        url_ddg = f"https://duckduckgo.com/html/?q=site%3Abesteveralbums.com+{nombre_para_url}+artist"
        respuesta = scraper.get(url_ddg, timeout=15)
        if respuesta.status_code == 200:
            sopa = BeautifulSoup(respuesta.text, 'html.parser')
            # Los resultados de DDG enlazan a las URLs externas
            for enlace in sopa.find_all('a', href=re.compile(r'besteveralbums\.com.*thechart\.php\?b=\d+')):
                href = enlace.get('href', '')
                # Limpiar URL si DDG la devuelve envuelta en redirector
                match = re.search(r'(https?://[^&\s]*besteveralbums\.com/thechart\.php\?b=\d+)', href)
                if match:
                    return match.group(1)
                if 'besteveralbums.com' in href:
                    return href
    except Exception:
        pass

    return None


def _extraer_average_rating(texto):
    """
    Busca 'Average Rating: X/100 (from N votes)'.
    """
    # Patrón principal con votos
    match = re.search(
        r'Average Rating[^\d]*([\d\.]+)\s*/\s*100\s*\(from\s*([\d,]+)\s*votes?\)',
        texto, re.IGNORECASE
    )
    if match:
        try:
            return float(match.group(1)), int(match.group(2).replace(',', ''))
        except ValueError:
            pass

    # Sin paréntesis de votos
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


def _datos_estimados(nombre_artista):
    semilla = int(hashlib.md5(nombre_artista.lower().encode()).hexdigest(), 16)
    return {
        "plataforma": "BestEverAlbums (Mock)",
        "nombre": nombre_artista,
        "num_charts": 50 + (semilla % 5000),
        "num_ratings": 10 + (semilla % 500),
        "pais": None,
        "nota_normalizada": round(40 + (semilla % 6000) / 100, 1),
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
        respuesta = scraper.get(url_artista, timeout=15)
        if respuesta.status_code != 200:
            print(f"BEA respondió {respuesta.status_code}. Usando datos estimados (RNF.5).")
            return _datos_estimados(nombre_artista)

        sopa = BeautifulSoup(respuesta.text, 'html.parser')
        texto = re.sub(r'\s+', ' ', sopa.get_text(' ', strip=True))

        nota_real, num_votos = _extraer_average_rating(texto)
        num_charts, num_ratings_globales, pais = _extraer_stats_globales(texto)

        if nota_real is None and num_charts is None and num_ratings_globales is None:
            print("BEA: HTML no parseable. Usando datos estimados (RNF.5).")
            return _datos_estimados(nombre_artista)

        if nota_real is not None:
            nota_normalizada = round(float(nota_real), 1)
            num_ratings_usar = num_votos if num_votos is not None else (num_ratings_globales or 0)
            print(f"BEA: Average Rating real = {nota_real}/100 (de {num_ratings_usar} votos), charts={num_charts}")
        else:
            num_ratings_usar = num_ratings_globales or 0
            if num_charts and num_charts > 0:
                nota_normalizada = round(min(100.0, (math.log10(num_charts) / 4.0) * 100), 1)
            else:
                nota_normalizada = 0.0
            print(f"BEA: nota agregada no disponible, derivada de charts={num_charts} -> {nota_normalizada}")

        return {
            "plataforma": "BestEverAlbums",
            "nombre": nombre_artista,
            "num_charts": num_charts or 0,
            "num_ratings": num_ratings_usar,
            "pais": pais,
            "nota_normalizada": nota_normalizada,
            "url": url_artista,
            "es_mock": False,
        }

    except Exception as e:
        print(f"BEA: excepción ({e}). Usando datos estimados (RNF.5).")
        return _datos_estimados(nombre_artista)


if __name__ == "__main__":
    for nombre in ["Radiohead", "Daft Punk", "MIKE", "Pink Floyd"]:
        print("---")
        print(extraer_datos_besteveralbums(nombre))