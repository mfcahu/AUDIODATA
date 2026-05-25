# 1. Le decimos a Google que use una imagen oficial de Python ligera
FROM python:3.10-slim

# 2. Configuraciones para que Python no guarde archivos basura en la nube
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Creamos la carpeta principal de la app dentro del servidor de Google
WORKDIR /app

# 4. Copiamos el archivo de librerías e instalamos todo en el servidor
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos el resto de nuestro código al servidor
COPY . .

# 6. Google Cloud Run usa el puerto 8080 por defecto para mostrar las webs
EXPOSE 8080

# 7. Comando definitivo: enciende la web usando el motor profesional Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "audiodata_web.app:app"]