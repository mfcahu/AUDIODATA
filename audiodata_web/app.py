from flask import Flask, jsonify
import sys
import os

# Truco para que Python encuentre nuestras otras carpetas del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importamos nuestras herramientas (Exploradores y Fábrica)
from audiodata_integrations.lastfm_client import obtener_datos_lastfm
from audiodata_integrations.rym_scraper import extraer_datos_rym
from audiodata_core.normalizador import normalizar_datos

app = Flask(__name__)

# Ruta 1: La página de inicio
@app.route('/')
def inicio():
    return "<h1>¡Bienvenido al sistema AUDIODATA!</h1><p>El backend de Flask está funcionando.</p>"

# Ruta 2: La API interna que busca y unifica los datos de un artista
@app.route('/api/artista/<nombre_artista>')
def buscar_artista(nombre_artista):
    print(f"\n--- Nueva petición web para: {nombre_artista} ---")
    
    # 1. Extracción (Capa de Integración)
    datos_lastfm = obtener_datos_lastfm(nombre_artista)
    datos_rym = extraer_datos_rym(nombre_artista)
    
    # 2. Transformación (Capa de Negocio)
    artista_unificado = normalizar_datos(nombre_artista, datos_lastfm, datos_rym)
    
    # 3. Presentación (Devolvemos los datos al navegador en formato JSON)
    return jsonify(artista_unificado)

if __name__ == '__main__':
    # Arrancamos el servidor local
    app.run(debug=True)