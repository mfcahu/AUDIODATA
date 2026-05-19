def normalizar_datos(nombre_artista, datos_lastfm, datos_rym, datos_discogs):
    # Añadimos un apartado de "enlaces" para guardar el ID de Discogs
    artista_global = {
        "nombre_canonico": nombre_artista,
        "metricas": {},
        "generos_consolidados": [],
        "enlaces": {} 
    }
    
    if datos_lastfm:
        artista_global["metricas"]["lastfm_oyentes"] = int(datos_lastfm['artist']['stats']['listeners'])
    
    if datos_rym:
        nota_original = datos_rym['nota_media']
        artista_global["metricas"]["rym_nota_original"] = nota_original
        artista_global["metricas"]["rym_nota_normalizada"] = nota_original * 20
        if "descriptores" in datos_rym:
            artista_global["generos_consolidados"].extend(datos_rym["descriptores"])
            
    # Nueva regla: Procesamos Discogs
    if datos_discogs:
        artista_global["enlaces"]["discogs_id"] = datos_discogs.get("id_discogs")
            
    return artista_global