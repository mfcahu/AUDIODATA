from flask import Flask, render_template, request, redirect, url_for
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audiodata_integrations.lastfm_client import obtener_datos_lastfm, obtener_top_albums_lastfm
from audiodata_integrations.all_music_scrapper import extraer_datos_allmusic
from audiodata_integrations.discogs_client import obtener_datos_discogs, obtener_top_albums_discogs
from audiodata_integrations.bestalbumever_scrapper import extraer_datos_besteveralbums
from audiodata_core.normalizador import normalizar_datos
from audiodata_persistence.db_repository import verificar_cache, guardar_en_cache

app = Flask(__name__)

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def procesar_busqueda():
    artista_buscado = request.form.get('artista') 
    return redirect(url_for('buscar_artista', nombre_artista=artista_buscado))

@app.route('/api/artista/<nombre_artista>')
def buscar_artista(nombre_artista):
    print(f"\n=== Nueva solicitud web para: {nombre_artista} ===")
    artista_unificado = verificar_cache(nombre_artista)
    
    if artista_unificado is None:
        # Datos de artista (información general)
        datos_lastfm = obtener_datos_lastfm(nombre_artista)
        datos_all_music = extraer_datos_allmusic(nombre_artista)
        datos_discogs = obtener_datos_discogs(nombre_artista)
        datos_bea = extraer_datos_besteveralbums(nombre_artista)
        
        # Top álbumes por fuente (para la comparativa)
        top_lastfm = obtener_top_albums_lastfm(nombre_artista, limite=3)
        top_discogs = obtener_top_albums_discogs(nombre_artista, limite=3)
        # AllMusic y BEA ya incluyen 'top_albums' dentro de su payload
        
        artista_unificado = normalizar_datos(
            nombre_artista,
            datos_lastfm, datos_all_music, datos_discogs, datos_bea,
            top_lastfm, top_discogs
        )
        guardar_en_cache(artista_unificado)
    
    return render_template('dashboard.html', artista=artista_unificado)

if __name__ == '__main__':
    app.run(debug=True)