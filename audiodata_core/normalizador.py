def normalizar_datos(nombre_artista, datos_lastfm, datos_rym, datos_discogs):
    # Creamos el molde vacío
    artista_global = {
        "nombre_canonico": nombre_artista,
        "metricas": {},
        "generos_consolidados": [],
        "enlaces": {} 
    }
    
    # 1. Procesamos Last.fm (¡Ahora también sacamos las etiquetas de aquí!)
    if datos_lastfm:
        artista_global["metricas"]["lastfm_oyentes"] = int(datos_lastfm['artist']['stats']['listeners'])
        
        # Extraemos las etiquetas reales y dinámicas de Last.fm
        lista_etiquetas = datos_lastfm['artist'].get('tags', {}).get('tag', [])
        for etiqueta in lista_etiquetas:
            artista_global["generos_consolidados"].append(etiqueta['name'])
    
    # 2. Procesamos Rate Your Music (Solo cogemos la nota, ignoramos sus etiquetas falsas)
    if datos_rym:
        nota_original = datos_rym['nota_media']
        artista_global["metricas"]["rym_nota_original"] = nota_original
        artista_global["metricas"]["rym_nota_normalizada"] = nota_original * 20
            
    # 3. Procesamos Discogs
    if datos_discogs:
        artista_global["enlaces"]["discogs_id"] = datos_discogs.get("id_discogs")
            
    return artista_global