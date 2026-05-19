import sqlite3
from datetime import datetime, timedelta

DB_PATH = "audiodata.db"

def inicializar_base_datos():
    """Crea la tabla de caché en la base de datos si no existe."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    # Creamos la tabla siguiendo los campos del Esquema Global (GCS)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache_artistas (
            nombre_artista TEXT PRIMARY KEY,
            lastfm_oyentes INTEGER,
            rym_nota_original REAL,
            rym_nota_normalizada REAL,
            generos TEXT,
            fecha_captura TEXT
        )
    ''')
    conexion.commit()
    conexion.close()

def verificar_cache(nombre_artista):
    """
    Consulta si el artista existe y está fresco (TTL de 24 horas).
    Devuelve el objeto unificado (GCS) o None si hay que buscarlo en internet.
    """
    inicializar_base_datos()
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    cursor.execute('''
        SELECT lastfm_oyentes, rym_nota_original, rym_nota_normalizada, generos, fecha_captura 
        FROM cache_artistas 
        WHERE LOWER(nombre_artista) = LOWER(?)
    ''', (nombre_artista,))
    
    fila = cursor.fetchone()
    conexion.close()
    
    if fila:
        lastfm_oyentes, rym_nota_original, rym_nota_normalizada, generos, fecha_captura_str = fila
        
        # Validamos el tiempo transcurrido (TTL diario de vuestra memoria)
        fecha_captura = datetime.strptime(fecha_captura_str, "%Y-%m-%d %H:%M:%S")
        if datetime.now() - fecha_captura < timedelta(hours=24):
            print(f"\n[BD] ¡Cache Hit! Cargando '{nombre_artista}' desde la base de datos...")
            return {
                "nombre_canonico": nombre_artista,
                "metricas": {
                    "lastfm_oyentes": lastfm_oyentes,
                    "rym_nota_original": rym_nota_original,
                    "rym_nota_normalizada": rym_nota_normalizada
                },
                "generos_consolidados": generos.split(",") if generos else []
            }
            
    print(f"\n[BD] Cache Miss: '{nombre_artista}' no está en la base de datos o caducó.")
    return None

def guardar_en_cache(artista_global):
    """Guarda o actualiza los datos unificados del artista en la base de datos."""
    inicializar_base_datos()
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    nombre = artista_global["nombre_canonico"]
    metricas = artista_global["metricas"]
    generos_str = ",".join(artista_global["generos_consolidados"])
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT OR REPLACE INTO cache_artistas 
        (nombre_artista, lastfm_oyentes, rym_nota_original, rym_nota_normalizada, generos, fecha_captura)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        nombre,
        metricas.get("lastfm_oyentes"),
        metricas.get("rym_nota_original"),
        metricas.get("rym_nota_normalizada"),
        generos_str,
        fecha_actual
    ))
    
    conexion.commit()
    conexion.close()
    print(f"[BD] Éxito: '{nombre}' guardado en la caché local.")