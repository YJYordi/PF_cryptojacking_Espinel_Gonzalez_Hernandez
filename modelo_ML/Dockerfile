FROM python:3.11-slim

WORKDIR /app

# ============================================
# OPTIMIZACIÓN: Instalar dependencias del sistema
# ============================================
# Instalar dependencias necesarias para usar wheels precompilados
# Esto evita que pip compile desde fuente (mucho más lento)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# OPTIMIZACIÓN: Instalar dependencias Python
# ============================================
# Copiar SOLO requirements.txt primero (mejor uso de caché de Docker)
# Si requirements.txt no cambia, Docker reutiliza esta capa completa
COPY requirements.txt .

# Actualizar pip y usar wheels precompilados (MUCHO más rápido)
# Separar dependencias pesadas (requieren compilación) de las ligeras
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir numpy>=1.24.0 pandas>=2.0.0 scikit-learn>=1.3.0 && \
    pip install --no-cache-dir psutil>=5.9.0 openai>=1.0.0 requests>=2.31.0

# ============================================
# OPTIMIZACIÓN: Copiar código (cambia frecuentemente)
# ============================================
# Copiar código del proyecto
# Nota: modelos y datos se montan como volúmenes, no se copian
COPY *.py ./
COPY scripts/ scripts/
COPY docker-entrypoint.sh ./
COPY README.md ./

# Crear directorios necesarios
RUN mkdir -p data models

# Variables de entorno
ENV PYTHONUNBUFFERED=1

# Script de inicio
RUN chmod +x docker-entrypoint.sh
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "pipeline_monitor.py"]

