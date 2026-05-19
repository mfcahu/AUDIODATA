def normalizar_datos(nombre_artista, datos_lastfm, datos_rym):
    """
    Toma los datos crudos de las diferentes fuentes y los unifica 
    en el Esquema Global (GCS) del sistema.
    """
    # Creamos el "molde" vacío de nuestro artista unificado
    artista_global = {
        "nombre_canonico": nombre_artista,
        "metricas": {},
        "generos_consolidados": []
    }
    
    # 1. Procesamos y limpiamos los datos de Last.fm
    if datos_lastfm:
        # Extraemos el número y nos aseguramos de que sea un número entero (int)
        oyentes = int(datos_lastfm['artist']['stats']['listeners'])
        artista_global["metricas"]["lastfm_oyentes"] = oyentes
    
    # 2. Procesamos y normalizamos los datos de Rate Your Music
    if datos_rym:
        nota_original = datos_rym['nota_media']
        
        # APLICAMOS LA REGLA DEL GCS: Multiplicamos por 20 para escala 0-100
        nota_escala_100 = nota_original * 20
        
        # Guardamos ambas notas para tener el contexto
        artista_global["metricas"]["rym_nota_original"] = nota_original
        artista_global["metricas"]["rym_nota_normalizada"] = nota_escala_100
        
        # Añadimos los descriptores al listado de géneros
        if "descriptores" in datos_rym:
            artista_global["generos_consolidados"].extend(datos_rym["descriptores"])
            
    return artista_global

# Bloque de prueba local
if __name__ == "__main__":
    # Simulamos los datos crudos que nos devolverían nuestros módulos de integración
    mock_lastfm = {'artist': {'stats': {'listeners': '7257848'}}}
    mock_rym = {'plataforma': 'Rate Your Music', 'nombre': 'Queen', 'nota_media': 4.2, 'descriptores': ['classic', 'rock', 'anthemic']}
    
    # Pasamos los datos por nuestra fábrica
    resultado = normalizar_datos("Queen", mock_lastfm, mock_rym)
    
    print("--- OBJETO ARTISTA UNIFICADO (GCS) ---")
    print(f"Nombre: {resultado['nombre_canonico']}")
    print(f"Oyentes Last.fm: {resultado['metricas'].get('lastfm_oyentes')}")
    print(f"Nota RYM Original: {resultado['metricas'].get('rym_nota_original')}/5")
    print(f"Nota RYM Normalizada: {resultado['metricas'].get('rym_nota_normalizada')}/100")
    print(f"Etiquetas: {resultado['generos_consolidados']}")