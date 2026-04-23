# Dockerfile - Define la imagen Docker para la aplicación Python
# Construye con: docker build -t riego-app .
# Ejecuta con: docker run -p 8501:8501 riego-app

# Usa imagen base de Python ligera
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de dependencias primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Expone el puerto que usa Streamlit (por defecto 8501)
EXPOSE 8501

# Comando para ejecutar ambos procesos: main.py en background + streamlit en foreground
CMD ["sh", "-c", "python app/main.py & streamlit run app/dashboard.py --server.port 8501 --server.address 0.0.0.0"]