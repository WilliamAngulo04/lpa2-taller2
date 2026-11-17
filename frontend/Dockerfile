# Imagen base oficial de Python
FROM python:3.12-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de requirements primero (mejor cache de Docker)
COPY ./app/requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY ./app .

# Exponer puerto
EXPOSE 3000

# Comando de arranque (servidor WSGI de producción)
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "2", "--timeout", "60", "main:app"]
