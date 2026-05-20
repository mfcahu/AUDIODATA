def normalizar_datos(nombre_artista, datos_lastfm, datos_rym, datos_discogs):
    artista_global = {
        "nombre_canonico": nombre_artista,
        "metricas": {},
        "generos_consolidados": [],
        "enlaces": {} 
    }
    
    if datos_lastfm:
        artista_global["metricas"]["lastfm_oyentes"] = int(datos_lastfm['artist']['stats']['listeners'])
        for etiqueta in datos_lastfm['artist'].get('tags', {}).get('tag', []):
            artista_global["generos_consolidados"].append(etiqueta['name'])
    
    if datos_rym:
        nota_original = datos_rym['nota_media']
        artista_global["metricas"]["rym_nota_original"] = nota_original
        artista_global["metricas"]["rym_nota_normalizada"] = nota_original * 20
            
    if datos_discogs:
        artista_global["enlaces"]["discogs_id"] = datos_discogs.get("id_discogs")
        artista_global["enlaces"]["imagen_url"] = datos_discogs.get("imagen") # ¡NUEVO: Pasamos la imagen a la web!
            
    return artista_global