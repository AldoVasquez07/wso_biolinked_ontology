# =================================================================
# Dockerfile para Backend Flask + RDFLib
# Ubicación: back_biolinked_ontology/Dockerfile
# =================================================================

FROM python:3.11-slim

# Metadatos
LABEL maintainer="aldo.vasq.lop@gmail.com"
LABEL description="BioLinkedCatalog Backend API"

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias (mínimas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar requirements primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar archivos específicos necesarios
COPY app.py .
COPY wsgi.py .
COPY biodiversity_catalog.ttl .

# Crear directorio para datos si no existe
RUN mkdir -p /app/data /app/logs

# Exponer puerto
EXPOSE 5000

# Variables de entorno
ENV FLASK_APP=wsgi.py
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Usuario no-root por seguridad
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Comando de inicio con gunicorn usando wsgi:app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "120", "wsgi:app"]