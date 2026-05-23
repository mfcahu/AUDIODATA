import sqlite3
from datetime import datetime, timedelta

DB_PATH = "audiodata.db"

def inicializar_base_datos():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache_artistas (
            nombre_artista TEXT PRIMARY KEY,
            lastfm_oyentes INTEGER,
            rym_nota_original REAL,
            rym_nota_normalizada REAL,
            discogs_id INTEGER,
            imagen_url TEXT,
            bea_num_charts INTEGER,
            bea_num_ratings INTEGER,
            bea_nota_normalizada REAL,
            bea_pais TEXT,
            generos TEXT,
            fecha_captura TEXT
        )
    ''')
    # Para BDs antiguas, añadimos columnas nuevas si no existen
    columnas_nuevas = [
        ("bea_num_charts", "INTEGER"),
        ("bea_num_ratings", "INTEGER"),
        ("bea_nota_normalizada", "REAL"),
        ("bea_pais", "TEXT"),
    ]
    for nombre_col, tipo_col in columnas_nuevas:
        try:
            cursor.execute(f"ALTER TABLE cache_artistas ADD COLUMN {nombre_col} {tipo_col}")
        except sqlite3.OperationalError:
            pass  # La columna ya existe
    
    conexion.commit()
    conexion.close()

def verificar_cache(nombre_artista):
    inicializar_base_datos()
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    cursor.execute('''
        SELECT lastfm_oyentes, rym_nota_original, rym_nota_normalizada, discogs_id, imagen_url,
               bea_num_charts, bea_num_ratings, bea_nota_normalizada, bea_pais,
               generos, fecha_captura 
        FROM cache_artistas WHERE LOWER(nombre_artista) = LOWER(?)
    ''', (nombre_artista,))
    fila = cursor.fetchone()
    conexion.close()
    
    if fila:
        (oyentes, nota_orig, nota_norm, d_id, img_url,
         bea_charts, bea_ratings, bea_nota, bea_pais,
         generos, fecha_str) = fila
        fecha_captura = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        if datetime.now() - fecha_captura < timedelta(hours=24):
            print(f"\n[BD] ¡Cache Hit! Cargando '{nombre_artista}' desde la base de datos...")
            enlaces = {"discogs_id": d_id, "imagen_url": img_url}
            if bea_pais:
                enlaces["bea_pais"] = bea_pais
            return {
                "nombre_canonico": nombre_artista,
                "metricas": {
                    "lastfm_oyentes": oyentes,
                    "rym_nota_original": nota_orig,
                    "rym_nota_normalizada": nota_norm,
                    "bea_num_charts": bea_charts or 0,
                    "bea_num_ratings": bea_ratings or 0,
                    "bea_nota_normalizada": bea_nota or 0.0,
                },
                "enlaces": enlaces,
                "generos_consolidados": generos.split(",") if generos else []
            }
    return None

def guardar_en_cache(artista_global):
    inicializar_base_datos()
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    nombre = artista_global["nombre_canonico"]
    metricas = artista_global["metricas"]
    enlaces = artista_global.get("enlaces", {})
    generos_str = ",".join(artista_global["generos_consolidados"])
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT OR REPLACE INTO cache_artistas 
        (nombre_artista, lastfm_oyentes, rym_nota_original, rym_nota_normalizada, discogs_id, imagen_url,
         bea_num_charts, bea_num_ratings, bea_nota_normalizada, bea_pais,
         generos, fecha_captura)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        nombre,
        metricas.get("lastfm_oyentes"),
        metricas.get("rym_nota_original"),
        metricas.get("rym_nota_normalizada"),
        enlaces.get("discogs_id"),
        enlaces.get("imagen_url"),
        metricas.get("bea_num_charts"),
        metricas.get("bea_num_ratings"),
        metricas.get("bea_nota_normalizada"),
        enlaces.get("bea_pais"),
        generos_str,
        fecha_actual,
    ))
    conexion.commit()
    conexion.close()