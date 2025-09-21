# ============================================
# STAGE 1: BUILDER (Construcción y dependencias)
# ============================================
FROM python:3.13-slim as builder

# Instalar dependencias del sistema necesarias para compilación
# gcc, g++, build-essential: Para compilar paquetes Python con extensiones en C
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# OPCIÓN A: Usar pip tradicional (más estable)
# Copiar archivo de dependencias
COPY pyproject.toml .

# Instalar todas las dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# OPCIÓN B (alternativa): Si quieres usar uv para velocidad
# RUN pip install uv && \
#     uv pip install --system .

# ============================================
# STAGE 2: RUNTIME (Imagen final optimizada)
# ============================================
FROM python:3.13-slim

# Instalar dependencias de runtime necesarias
# tesseract-ocr: Para OCR de PDFs escaneados
# tesseract-ocr-spa: Idioma español para OCR
# libgl1-mesa-glx, etc.: Bibliotecas para procesamiento de imágenes (PIL/Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar las bibliotecas Python instaladas desde el builder
# Esto copia todos los paquetes sin necesidad de reinstalar
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && \
    mkdir -p /tmp/finapp_storage/docs && \
    chown -R appuser:appuser /tmp/finapp_storage

# Establecer directorio de trabajo
WORKDIR /app

# Copiar código de la aplicación
COPY --chown=appuser:appuser finapp/ ./finapp/

# Copiar script de inicio
COPY --chown=appuser:appuser start.sh .
RUN chmod +x start.sh

# ============================================
# VARIABLES DE ENTORNO
# ============================================

# Variables FIJAS que siempre son iguales en Cloud Run
ENV PORT=8080
ENV API_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Variables que indican que estamos en Cloud Run (para tu settings.py)
# K_SERVICE será sobrescrito por Cloud Run, pero lo ponemos para testing local
ENV K_SERVICE=finapp-docker

# IMPORTANTE: Las variables específicas de tu proyecto NO van aquí
# Se configuran en Cloud Run con --env-vars-file o --set-env-vars
# Esto incluye: GCP_PROJECT, GCP_LOCATION, VERTEX_MODEL_ID, GCS_BUCKET, etc.

# Cambiar al usuario no-root
USER appuser

# Exponer puerto (informativo, Cloud Run lo ignora y usa PORT)
EXPOSE 8080

# Health check (opcional pero recomendado)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/docs || exit 1

# Comando de inicio
# Shell form para que las variables de entorno se expandan correctamente
CMD ["./start.sh"]

# ============================================
# NOTAS DE BUILD:
# Para construir: docker build -t finapp .
# Para probar local: docker run -p 8080:8080 --env-file .env finapp
# Para Cloud Run: Se despliega con gcloud run deploy
# ============================================