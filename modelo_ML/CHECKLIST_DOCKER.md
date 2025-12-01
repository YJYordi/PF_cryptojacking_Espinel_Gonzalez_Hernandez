# ✅ Checklist Pre-Docker Compose

## Antes de ejecutar `docker compose up --build`

### 1. Modelos Entrenados ✓
- [x] `models/rf_model.pkl` existe
- [x] `models/scaler.pkl` existe
- [x] `models/iso_model.pkl` existe (opcional)

**Verificación:**
```bash
cd modelo_ML
ls -lh models/*.pkl
```

### 2. Archivos Docker ✓
- [x] `Dockerfile` existe y es válido
- [x] `docker-entrypoint.sh` existe y es ejecutable
- [x] `requirements.txt` existe
- [x] `pipeline_monitor.py` existe

### 3. Configuración Docker Compose ✓
- [x] `docker-compose.yml` está en `PF_backend/ProyectoFinal_Backend/`
- [x] Rutas de volúmenes son correctas (`../../modelo_ML/models`)
- [x] Variables de entorno configuradas

### 4. Variables de Entorno

Edita `.env` en `PF_backend/ProyectoFinal_Backend/`:

```env
# Agregar estas líneas si no existen:
OPENAI_API_KEY=tu-api-key-aqui
ML_INTERVAL_SECONDS=10
EVE_JSON_PATH=/var/log/suricata/eve.json
```

### 5. Verificación Final

```bash
# 1. Verificar que docker-compose.yml es válido
cd PF_backend/ProyectoFinal_Backend
docker compose config > /dev/null && echo "✓ docker-compose.yml válido"

# 2. Verificar que los modelos existen
ls ../../modelo_ML/models/*.pkl

# 3. Verificar que el Dockerfile existe
ls ../../modelo_ML/Dockerfile
```

## 🚀 Ejecutar

```bash
cd PF_backend/ProyectoFinal_Backend
docker compose up --build
```

## 📊 Monitoreo

```bash
# Ver logs del servicio ML
docker compose logs -f ml-pipeline

# Ver estado de todos los servicios
docker compose ps
```

## ⚠️ Problemas Comunes

### Error: "Modelos no encontrados"
**Solución:** Los modelos deben estar en `modelo_ML/models/` antes de ejecutar docker compose.

### Error: "OPENAI_API_KEY no está configurada"
**Solución:** Agrega `OPENAI_API_KEY=...` al archivo `.env`.

### Error: "Backend no está disponible"
**Solución:** Espera a que el servicio `app` inicie completamente. El script espera automáticamente hasta 60 segundos.

