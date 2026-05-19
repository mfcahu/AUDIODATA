from flask import Flask, render_template, request, redirect, url_for
import sys
import os

# Ajuste de rutas para conectar los módulos de las carpetas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audiodata_integrations.lastfm_client import obtener_datos_lastfm
from audiodata_integrations.rym_scraper import extraer_datos_rym
from audiodata_core.normalizador import normalizar_datos
from audiodata_persistence.db_repository import verificar_cache, guardar_en_cache

app = Flask(__name__)

# Ruta 1: La página de inicio (Muestra el buscador)
@app.route('/')
def inicio():
    return render_template('index.html')

# Ruta 2: Recibe el texto del formulario y redirige a la página del artista
@app.route('/buscar', methods=['POST'])
def procesar_busqueda():
    # 'artista' es el nombre que le dimos a la cajita de texto en el HTML
    artista_buscado = request.form.get('artista') 
    
    # Redirigimos automáticamente a la ruta de análisis que ya teníamos creada
    return redirect(url_for('buscar_artista', nombre_artista=artista_buscado))

# Ruta 3: La API interna que busca, unifica y muestra los datos del artista
@app.route('/api/artista/<nombre_artista>')
def buscar_artista(nombre_artista):
    print(f"\n=== Nueva solicitud web para: {nombre_artista} ===")
    
    artista_unificado = verificar_cache(nombre_artista)
    
    if artista_unificado is None:
        datos_lastfm = obtener_datos_lastfm(nombre_artista)
        datos_rym = extraer_datos_rym(nombre_artista)
        
        artista_unificado = normalizar_datos(nombre_artista, datos_lastfm, datos_rym)
        guardar_en_cache(artista_unificado)
    
    return render_template('dashboard.html', artista=artista_unificado)

if __name__ == '__main__':
    app.run(debug=True)