FROM python:3.10-slim

WORKDIR /app

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Crear directorio de logs
RUN mkdir -p logs

# Exponer el puerto de la API
EXPOSE 8000

# Comando para ejecutar la API
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"] 