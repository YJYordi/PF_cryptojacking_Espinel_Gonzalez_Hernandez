#!/bin/bash
set -e

echo "=========================================="
echo "Sistema de Detección de Cryptojacking ML"
echo "=========================================="

# Esperar a que el backend esté disponible
echo "[INFO] Esperando a que el backend esté disponible..."
BACKEND_URL=${BACKEND_URL:-http://app:8080}
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s "${BACKEND_URL}/healthz" > /dev/null 2>&1; then
        echo "[INFO] ✅ Backend está disponible"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "[INFO] Intento $RETRY_COUNT/$MAX_RETRIES: Backend no disponible aún, esperando..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "[WARNING] Backend no está disponible después de $MAX_RETRIES intentos"
    echo "[WARNING] Continuando de todas formas..."
fi

# Verificar que los modelos existan
if [ ! -f "models/rf_model.pkl" ] || [ ! -f "models/scaler.pkl" ]; then
    echo "[ERROR] ❌ Modelos no encontrados en models/"
    echo "[ERROR] Los modelos son requeridos para que el pipeline funcione"
    echo "[INFO] Entrena los modelos primero:"
    echo "  1. cd modelo_ML"
    echo "  2. python scripts/generate_synthetic_dataset.py"
    echo "  3. python train_model.py"
    echo "[INFO] O monta los modelos como volumen en docker-compose.yml"
    exit 1
fi

echo "[INFO] ✅ Modelos encontrados:"
ls -lh models/*.pkl 2>/dev/null || echo "  (no se pudieron listar)"

# El analizador de eventos EVE no requiere API key externa
echo "[INFO] ✅ Analizador de eventos EVE configurado (no requiere API key externa)"

echo "[INFO] Iniciando pipeline de monitoreo..."
echo "=========================================="

# Construir comando con variables de entorno
BACKEND_URL=${BACKEND_URL:-http://app:8080}
EVE_JSON_PATH=${EVE_JSON_PATH:-/var/log/suricata/eve.json}
SURICATA_RULES_FILE=${SURICATA_RULES_FILE:-/var/log/suricata/rules/generated.rules}
INTERVAL_SECONDS=${INTERVAL_SECONDS:-10}

# Ejecutar pipeline con parámetros
exec python pipeline_monitor.py \
    --backend-url "${BACKEND_URL}" \
    --eve-json "${EVE_JSON_PATH}" \
    --suricata-rules-file "${SURICATA_RULES_FILE}" \
    --interval "${INTERVAL_SECONDS}"

