# 🐳 Instrucciones para Docker

## ✅ Checklist Antes de Ejecutar

### 1. Modelos Entrenados
```bash
cd modelo_ML
# Si no tienes modelos, entrénalos:
python scripts/generate_synthetic_dataset.py
python train_model.py
```

**Verificar que existan:**
- `models/rf_model.pkl` ✓
- `models/scaler.pkl` ✓
- `models/iso_model.pkl` (opcional)

### 2. Configurar Variables de Entorno

Edita el archivo `.env` en `PF_backend/ProyectoFinal_Backend/`:

```env
# Base de datos (ya debería estar)
DATABASE_URL="postgresql://postgres:postgres@db:5432/ids?schema=public"
NATS_URL="nats://nats:4222"
PORT=8080
NODE_ENV=production

# ⭐ AGREGAR ESTAS LÍNEAS:
OPENAI_API_KEY=tu-api-key-aqui
ML_INTERVAL_SECONDS=10
EVE_JSON_PATH=/var/log/suricata/eve.json
```

### 3. Verificar Estructura

```
modelo_ML/
├── models/
│   ├── rf_model.pkl    ✓ Debe existir
│   └── scaler.pkl      ✓ Debe existir
├── data/
│   └── dataset.csv     (opcional, solo para referencia)
├── Dockerfile          ✓
├── docker-entrypoint.sh ✓
└── pipeline_monitor.py ✓
```

## 🚀 Ejecutar

```bash
cd PF_backend/ProyectoFinal_Backend
docker compose up --build
```

## 📊 Verificar que Funciona

### 1. Ver logs del servicio ML:
```bash
docker compose logs -f ml-pipeline
```

Deberías ver:
```
[INFO] ✅ Backend está disponible
[INFO] Iniciando pipeline de monitoreo...
============================================================
PIPELINE DE MONITOREO DE CRYPTOJACKING
============================================================
```

### 2. Verificar que el servicio esté corriendo:
```bash
docker compose ps
```

Deberías ver `ml-pipeline` con estado `Up`.

### 3. Verificar que los modelos se cargaron:
```bash
docker compose logs ml-pipeline | grep "Modelo cargado"
```

## 🔧 Solución de Problemas

### Error: "Modelos no encontrados"
**Solución**: Los modelos deben estar en `models/` antes de construir la imagen, o se montarán desde el volumen.

**Opción 1**: Copiar modelos al volumen después de construir:
```bash
docker compose run --rm ml-pipeline python train_model.py
```

**Opción 2**: Montar modelos desde el host:
Edita `docker-compose.yml` y agrega:
```yaml
volumes:
  - ./modelo_ML/models:/app/models:ro
```

### Error: "OPENAI_API_KEY no está configurada"
**Solución**: Agrega la variable al archivo `.env` del backend.

### Error: "Backend no está disponible"
**Solución**: Verifica que el servicio `app` esté corriendo:
```bash
docker compose logs app
```

## 📝 Notas Importantes

1. **Los modelos se persisten en el volumen `ml_models`** - Si entrenas nuevos modelos dentro del contenedor, se guardarán ahí.

2. **El pipeline espera automáticamente al backend** - No necesitas iniciarlo manualmente.

3. **Los volúmenes son persistentes** - Los modelos y datos se mantienen entre reinicios.

4. **El servicio se reinicia automáticamente** - Si falla, Docker lo reiniciará.

