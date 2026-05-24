import sqlite3
import json
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
            top_albums_json TEXT,
            consenso_albums_json TEXT,
            fecha_captura TEXT
        )
    ''')
    # Migración para BDs antiguas
    columnas_nuevas = [
        ("bea_num_charts", "INTEGER"),
        ("bea_num_ratings", "INTEGER"),
        ("bea_nota_normalizada", "REAL"),
        ("bea_pais", "TEXT"),
        ("imagen_url", "TEXT"),
        ("top_albums_json", "TEXT"),
        ("consenso_albums_json", "TEXT"),
    ]
    for nombre_col, tipo_col in columnas_nuevas:
        try:
            cursor.execute(f"ALTER TABLE cache_artistas ADD COLUMN {nombre_col} {tipo_col}")
        except sqlite3.OperationalError:
            pass
    conexion.commit()
    conexion.close()


def verificar_cache(nombre_artista):
    inicializar_base_datos()
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT lastfm_oyentes, discogs_id, imagen_url,
               bea_num_charts, bea_num_ratings, bea_nota_normalizada, bea_pais,
               generos, top_albums_json, consenso_albums_json, fecha_captura 
        FROM cache_artistas WHERE LOWER(nombre_artista) = LOWER(?)
    ''', (nombre_artista,))
    fila = cursor.fetchone()
    conexion.close()

    if fila:
        (oyentes, d_id, img_url,
         bea_charts, bea_ratings, bea_nota, bea_pais,
         generos, top_json, consenso_json, fecha_str) = fila
        fecha_captura = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        if datetime.now() - fecha_captura < timedelta(hours=24):
            print(f"\n[BD] ¡Cache Hit! Cargando '{nombre_artista}' desde la base de datos...")
            enlaces = {"discogs_id": d_id, "imagen_url": img_url}
            if bea_pais:
                enlaces["bea_pais"] = bea_pais
            try:
                top_albums = json.loads(top_json) if top_json else {}
            except json.JSONDecodeError:
                top_albums = {}
            try:
                consenso = json.loads(consenso_json) if consenso_json else []
            except json.JSONDecodeError:
                consenso = []
            return {
                "nombre_canonico": nombre_artista,
                "metricas": {
                    "lastfm_oyentes": oyentes or 0,
                    "bea_num_charts": bea_charts or 0,
                    "bea_num_ratings": bea_ratings or 0,
                    "bea_nota_normalizada": bea_nota or 0.0,
                },
                "enlaces": enlaces,
                "generos_consolidados": generos.split(",") if generos else [],
                "top_albums_por_fuente": top_albums,
                "consenso_albums": consenso,
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
    top_json = json.dumps(artista_global.get("top_albums_por_fuente", {}), ensure_ascii=False)
    consenso_json = json.dumps(artista_global.get("consenso_albums", []), ensure_ascii=False)
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT OR REPLACE INTO cache_artistas 
        (nombre_artista, lastfm_oyentes, discogs_id, imagen_url,
         bea_num_charts, bea_num_ratings, bea_nota_normalizada, bea_pais,
         generos, top_albums_json, consenso_albums_json, fecha_captura)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        nombre,
        metricas.get("lastfm_oyentes"),
        enlaces.get("discogs_id"),
        enlaces.get("imagen_url"),
        metricas.get("bea_num_charts"),
        metricas.get("bea_num_ratings"),
        metricas.get("bea_nota_normalizada"),
        enlaces.get("bea_pais"),
        generos_str,
        top_json,
        consenso_json,
        fecha_actual,
    ))
    conexion.commit()
    conexion.close()