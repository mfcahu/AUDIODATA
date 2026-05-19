from flask import Flask, render_template
import sys
import os

# Ajuste de rutas para conectar los módulos de las carpetas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audiodata_integrations.lastfm_client import obtener_datos_lastfm
from audiodata_integrations.rym_scraper import extraer_datos_rym
from audiodata_core.normalizador import normalizar_datos
# Importamos la nueva capa de persistencia
from audiodata_persistence.db_repository import verificar_cache, guardar_en_cache

app = Flask(__name__)

@app.route('/')
def inicio():
    return "<h1>¡Bienvenido al sistema AUDIODATA!</h1>"

@app.route('/api/artista/<nombre_artista>')
def buscar_artista(nombre_artista):
    print(f"\n=== Nueva solicitud web para: {nombre_artista} ===")
    
    # 1. Intentar recuperar desde la Base de Datos (Caché)
    artista_unificado = verificar_cache(nombre_artista)
    
    # 2. Si no estaba en la base de datos (Cache Miss), vamos a buscar a Internet
    if artista_unificado is None:
        # Extracción externa
        datos_lastfm = obtener_datos_lastfm(nombre_artista)
        datos_rym = extraer_datos_rym(nombre_artista)
        
        # Transformación al esquema global (GCS)
        artista_unificado = normalizar_datos(nombre_artista, datos_lastfm, datos_rym)
        
        # Guardamos el resultado en la base de datos para la próxima vez
        guardar_en_cache(artista_unificado)
    
    # 3. Renderizamos la vista con los datos finales
    return render_template('dashboard.html', artista=artista_unificado)

if __name__ == '__main__':
    app.run(debug=True)