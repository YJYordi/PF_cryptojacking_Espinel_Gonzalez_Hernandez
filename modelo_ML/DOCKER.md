# Docker - Sistema de ML

## Configuración Docker

El sistema de ML está integrado en Docker y se ejecuta automáticamente al levantar los servicios.

## Variables de Entorno

Agrega estas variables a tu archivo `.env` en `ProyectoFinal_Backend/`:

```env
# OpenAI API Key (requerida para generación de reglas)
OPENAI_API_KEY=tu-api-key-aqui

# Ruta al archivo eve.json de Suricata (opcional)
EVE_JSON_PATH=/var/log/suricata/eve.json

# Intervalo de monitoreo en segundos (opcional, default: 10)
ML_INTERVAL_SECONDS=10
```

## Uso

### Levantar todos los servicios (incluyendo ML)

```bash
cd PF_backend/ProyectoFinal_Backend
docker compose up --build
```

### Solo servicios de infraestructura + ML

```bash
docker compose up db nats app ml-pipeline
```

### Ver logs del pipeline ML

```bash
docker compose logs -f ml-pipeline
```

### Reconstruir solo el servicio ML

```bash
docker compose build ml-pipeline
docker compose up ml-pipeline
```

## Volúmenes

El servicio ML usa los siguientes volúmenes:

- `suricata_logs`: Logs de Suricata (compartido, solo lectura)
- `ml_models`: Modelos entrenados (persistente)
- `ml_data`: Datasets (persistente)
- `ml_rules`: Reglas generadas (persistente)

## Inicio Automático

El servicio ML:
1. Espera a que el backend esté disponible
2. Verifica que los modelos existan
3. Inicia el pipeline de monitoreo automáticamente

## Notas

- Si los modelos no existen, el servicio intentará iniciar pero fallará
- Entrena los modelos primero: `python train_model.py` (fuera de Docker)
- O copia los modelos a `models/` antes de construir la imagen

