# ⚠️ Nota sobre Build Lento (Paso 39/48)

## ¿Por qué es lento?

El paso **39/48** está instalando las dependencias de Python más pesadas:
- `numpy` (~50-100MB, requiere compilación)
- `pandas` (~100-200MB, requiere compilación)
- `scikit-learn` (~50-100MB, requiere compilación)

**Tiempo estimado:** 5-15 minutos en la primera compilación.

## ¿Por qué compila desde fuente?

Aunque Python 3.11-slim debería tener wheels precompilados, a veces pip compila desde fuente si:
1. No encuentra wheels compatibles para tu arquitectura
2. Faltan dependencias del sistema
3. La versión específica no tiene wheels

## Soluciones

### ✅ Solución 1: Esperar (Recomendado)
**La primera vez es lenta, pero las siguientes builds serán MUCHO más rápidas** gracias al caché de Docker.

Si `requirements.txt` no cambia, Docker reutilizará la capa completa (paso 25-27).

### ✅ Solución 2: Usar BuildKit
```bash
DOCKER_BUILDKIT=1 docker compose build ml-pipeline
```

### ✅ Solución 3: Pre-construir imagen base
Si vas a hacer múltiples builds, puedes crear una imagen base:

```dockerfile
# Dockerfile.base
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl libc6-dev libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir numpy pandas scikit-learn
```

Luego en tu Dockerfile principal:
```dockerfile
FROM ml-base:latest
# ... resto del código
```

### ⚠️ Solución 4: Usar versión específica con wheels garantizados
Modifica `requirements.txt` para usar versiones que definitivamente tienen wheels:

```
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.0
```

## Monitoreo del Build

Puedes ver qué está haciendo exactamente:
```bash
docker compose build --progress=plain ml-pipeline
```

## Consejo Final

**Deja que termine la primera vez.** Una vez que termine, los builds siguientes serán mucho más rápidos (30-60 segundos) porque Docker cacheará las capas de instalación.

