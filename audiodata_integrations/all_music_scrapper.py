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


def _extraer_jsonld_grupo(sopa):
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
    nombre_clase = etiqueta.lower().replace(' ', '-')
    for sel in [f'div.{nombre_clase}', f'section.{nombre_clase}']:
        div = sopa.select_one(sel)
        if div:
            items = [a.get_text(strip=True) for a in div.find_all('a')]
            items = [i for i in items if i]
            if items:
                return items
    encabezado = sopa.find(['h4', 'h3', 'h2', 'div'], string=re.compile(rf'^\s*{re.escape(etiqueta)}\s*$', re.IGNORECASE))
    if encabezado:
        siguiente = encabezado.find_next_sibling()
        if siguiente:
            items = [a.get_text(strip=True) for a in siguiente.find_all('a')]
            return [i for i in items if i]
    return []


def _nombre_desde_url_album(url_album):
    match = re.search(r'/album/([^/]+?)(?:-mw\d+)?/?$', url_album)
    if not match:
        return ""
    slug = match.group(1)
    slug = re.sub(r'-mw\d+$', '', slug)
    palabras = slug.split('-')
    minusculas = {'a', 'an', 'the', 'of', 'in', 'on', 'and', 'or', 'for', 'to', 'with'}
    resultado = []
    for i, p in enumerate(palabras):
        if not p:
            continue
        if i > 0 and p.lower() in minusculas:
            resultado.append(p.lower())
        else:
            resultado.append(p.capitalize())
    return ' '.join(resultado)


def _es_allmusic_pick(enlace, padre):
    """
    Detecta si el álbum tiene la marca 'AllMusic Pick' (la estrella roja).
    Aparece como una imagen o icono cerca del enlace al álbum.
    """
    if padre:
        # Buscar imagen con 'pick' en el alt/src/class, o un span con clase pick
        texto = padre.get_text(' ', strip=True).lower()
        if 'allmusic pick' in texto or 'editor pick' in texto:
            return True
        for img in padre.find_all('img'):
            alt = (img.get('alt', '') or '').lower()
            src = (img.get('src', '') or '').lower()
            if 'pick' in alt or 'pick' in src or 'star' in alt:
                return True
        for span in padre.find_all(class_=True):
            clases = ' '.join(span.get('class', [])).lower()
            if 'pick' in clases:
                return True
    return False


def _extraer_top_albums(scraper, url_artista, limite=3):
    """
    Visita /{id}/discography y extrae los primeros álbumes.
    Para cada álbum, intenta capturar: nombre, año, imagen, AllMusic Pick.
    """
    url_disco = url_artista.rstrip('/') + '/discography'
    try:
        respuesta = scraper.get(url_disco, timeout=15)
        if respuesta.status_code != 200:
            print(f"AllMusic /discography: status {respuesta.status_code}")
            return []
        sopa = BeautifulSoup(respuesta.text, 'html.parser')

        resultado = []
        vistos = set()

        for enlace in sopa.find_all('a', href=re.compile(r'/album/')):
            if len(resultado) >= limite:
                break

            href = enlace['href']
            nombre = enlace.get_text(strip=True)
            if not nombre:
                nombre = _nombre_desde_url_album(href)
            if not nombre or len(nombre) < 2:
                continue

            clave = nombre.lower()
            if clave in vistos:
                continue
            vistos.add(clave)

            padre = enlace.find_parent(['tr', 'div', 'li', 'article'])

            # Año
            year = None
            if padre:
                m = re.search(r'\b(19[3-9]\d|20\d{2})\b', padre.get_text(' ', strip=True))
                if m:
                    year = int(m.group(1))

            # Imagen
            imagen = ""
            img = enlace.find('img') or (padre.find('img') if padre else None)
            if img:
                imagen = img.get('data-src') or img.get('src', '') or img.get('data-original', '')

            # AllMusic Pick (insignia editorial)
            es_pick = _es_allmusic_pick(enlace, padre)

            url_album = href if href.startswith('http') else BASE_URL + href
            resultado.append({
                "nombre": nombre,
                "year": year,
                "imagen": imagen,
                "url": url_album,
                "es_pick": es_pick,
            })

        return resultado

    except Exception as e:
        print(f"AllMusic discography: error {e}")
        return []


def _datos_estimados(nombre_artista):
    semilla = int(hashlib.md5(nombre_artista.lower().encode()).hexdigest(), 16)
    pools = [
        ["rock", "classic rock"], ["indie", "alternative"], ["electronic", "dance"],
        ["pop"], ["hip hop"], ["jazz"], ["folk", "acoustic"], ["metal"],
    ]
    return {
        "plataforma": "AllMusic (Mock)",
        "nombre": nombre_artista,
        "descriptores": pools[semilla % len(pools)],
        "top_albums": [],
        "es_mock": True,
    }


def extraer_datos_allmusic(nombre_artista):
    print(f"Buscando '{nombre_artista}' en AllMusic...")
    try:
        scraper = _crear_scraper()
        url_artista = _buscar_url_artista(scraper, nombre_artista)
        if not url_artista:
            print("AllMusic: no se localizó al artista. Usando datos estimados (RNF.5).")
            return _datos_estimados(nombre_artista)

        print(f"AllMusic: ficha encontrada en {url_artista}")
        respuesta = scraper.get(url_artista, timeout=15)
        if respuesta.status_code != 200:
            print(f"AllMusic respondió {respuesta.status_code}. Usando datos estimados (RNF.5).")
            return _datos_estimados(nombre_artista)

        sopa = BeautifulSoup(respuesta.text, 'html.parser')

        jsonld = _extraer_jsonld_grupo(sopa)
        nombre_real = nombre_artista
        generos_jsonld = []
        if jsonld:
            nombre_real = jsonld.get('name', nombre_artista)
            g = jsonld.get('genre', [])
            generos_jsonld = [g] if isinstance(g, str) else list(g)

        generos = _extraer_seccion(sopa, 'Genre') or generos_jsonld
        estilos = _extraer_seccion(sopa, 'Styles')
        descriptores = list(dict.fromkeys(generos + estilos))

        top_albums = _extraer_top_albums(scraper, url_artista)

        if not descriptores and not top_albums:
            print("AllMusic: ningún dato extraíble. Usando datos estimados (RNF.5).")
            return _datos_estimados(nombre_artista)

        print(f"AllMusic: {len(descriptores)} descriptores, {len(top_albums)} álbumes")
        return {
            "plataforma": "AllMusic",
            "nombre": nombre_real,
            "descriptores": descriptores,
            "top_albums": top_albums,
            "url": url_artista,
            "es_mock": False,
        }

    except Exception as e:
        print(f"AllMusic: excepción ({e}). Usando datos estimados (RNF.5).")
        return _datos_estimados(nombre_artista)


if __name__ == "__main__":
    print(extraer_datos_allmusic("Radiohead"))