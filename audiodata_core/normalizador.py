def normalizar_datos(nombre_artista, datos_lastfm, datos_allmusic, datos_discogs, datos_bea=None):
    artista_global = {
        "nombre_canonico": nombre_artista,
        "metricas": {},
        "generos_consolidados": [],
        "enlaces": {}
    }

    # 1. Last.fm: popularidad real (oyentes) + etiquetas dinámicas
    if datos_lastfm:
        try:
            artista_global["metricas"]["lastfm_oyentes"] = int(datos_lastfm['artist']['stats']['listeners'])
        except (KeyError, TypeError, ValueError):
            artista_global["metricas"]["lastfm_oyentes"] = 0
        for etiqueta in datos_lastfm.get('artist', {}).get('tags', {}).get('tag', []):
            if etiqueta.get('name'):
                artista_global["generos_consolidados"].append(etiqueta['name'])

    # 2. AllMusic: descriptores cualitativos (géneros + estilos)
    # NOTA: AllMusic ya no expone una nota agregada por artista, solo por álbum.
    # Esta fuente se usa exclusivamente para enriquecer los descriptores.
    if datos_allmusic:
        for d in datos_allmusic.get('descriptores', []):
            if d and d not in artista_global["generos_consolidados"]:
                artista_global["generos_consolidados"].append(d)

    # 3. Discogs: identidad universal (ID + imagen)
    if datos_discogs:
        artista_global["enlaces"]["discogs_id"] = datos_discogs.get("id_discogs")
        artista_global["enlaces"]["imagen_url"] = datos_discogs.get("imagen")

    # 4. BestEverAlbums: nota agregada real (X/100) + prestigio crítico
    if datos_bea:
        artista_global["metricas"]["bea_num_charts"] = datos_bea.get("num_charts", 0)
        artista_global["metricas"]["bea_num_ratings"] = datos_bea.get("num_ratings", 0)
        artista_global["metricas"]["bea_nota_normalizada"] = datos_bea.get("nota_normalizada", 0.0)
        if datos_bea.get("pais"):
            artista_global["enlaces"]["bea_pais"] = datos_bea["pais"]

    return artista_global