import re


def _normalizar_titulo(titulo):
    if not titulo:
        return ""
    t = re.sub(r'\s*[\(\[].*?[\)\]]', '', titulo)
    t = re.sub(r'\s*-\s*(deluxe|remaster.*|special.*|anniversary.*).*$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'[^\w\s]', '', t)
    return ' '.join(t.lower().split())


# Fuentes que entran en el cálculo de consenso (BEA queda fuera por su cobertura inestable)
FUENTES_CONSENSO = ("Last.fm", "AllMusic", "Discogs")


def _detectar_consenso(top_por_fuente):
    """
    Detecta álbumes que aparecen en al menos 2 de las 3 fuentes principales
    (Last.fm, AllMusic, Discogs). BEA queda fuera del cálculo.
    """
    apariciones = {}
    for fuente, albums in top_por_fuente.items():
        if fuente not in FUENTES_CONSENSO:
            continue
        if not albums:
            continue
        for album in albums:
            nombre = album.get("nombre", "")
            clave = _normalizar_titulo(nombre)
            if not clave:
                continue
            if clave not in apariciones:
                apariciones[clave] = {"nombre": nombre, "fuentes": set()}
            apariciones[clave]["fuentes"].add(fuente)

    consenso = [
        {"nombre": v["nombre"], "fuentes": sorted(v["fuentes"]), "num_fuentes": len(v["fuentes"])}
        for v in apariciones.values()
        if len(v["fuentes"]) >= 2
    ]
    consenso.sort(key=lambda x: -x["num_fuentes"])
    return consenso


def normalizar_datos(nombre_artista,
                     datos_lastfm, datos_allmusic, datos_discogs, datos_bea,
                     top_lastfm=None, top_discogs=None):
    artista_global = {
        "nombre_canonico": nombre_artista,
        "metricas": {},
        "generos_consolidados": [],
        "enlaces": {},
        "top_albums_por_fuente": {},
        "consenso_albums": [],
    }

    # 1. Last.fm
    if datos_lastfm:
        try:
            artista_global["metricas"]["lastfm_oyentes"] = int(datos_lastfm['artist']['stats']['listeners'])
        except (KeyError, TypeError, ValueError):
            artista_global["metricas"]["lastfm_oyentes"] = 0
        for etiqueta in datos_lastfm.get('artist', {}).get('tags', {}).get('tag', []):
            if etiqueta.get('name'):
                artista_global["generos_consolidados"].append(etiqueta['name'])

    # 2. AllMusic
    if datos_allmusic:
        for d in datos_allmusic.get('descriptores', []):
            if d and d not in artista_global["generos_consolidados"]:
                artista_global["generos_consolidados"].append(d)

    # 3. Discogs
    if datos_discogs:
        artista_global["enlaces"]["discogs_id"] = datos_discogs.get("id_discogs")
        artista_global["enlaces"]["imagen_url"] = datos_discogs.get("imagen")

    # 4. BEA
    if datos_bea:
        artista_global["metricas"]["bea_num_charts"] = datos_bea.get("num_charts", 0)
        artista_global["metricas"]["bea_num_ratings"] = datos_bea.get("num_ratings", 0)
        artista_global["metricas"]["bea_nota_normalizada"] = datos_bea.get("nota_normalizada", 0.0)
        if datos_bea.get("pais"):
            artista_global["enlaces"]["bea_pais"] = datos_bea["pais"]

    # 5. Top álbumes por fuente (BEA va para las métricas pero su top no se muestra
    #    en la comparativa porque su cobertura es muy inestable)
    top_por_fuente = {
        "Last.fm": top_lastfm or [],
        "AllMusic": (datos_allmusic or {}).get("top_albums", []),
        "Discogs": top_discogs or [],
    }
    artista_global["top_albums_por_fuente"] = top_por_fuente

    # 6. Detección de consenso (solo entre las 3 fuentes principales)
    artista_global["consenso_albums"] = _detectar_consenso(top_por_fuente)

    return artista_global