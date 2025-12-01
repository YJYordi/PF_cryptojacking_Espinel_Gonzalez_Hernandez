#!/bin/bash
# Script para eliminar reglas generadas automáticamente

BACKEND_URL=${BACKEND_URL:-http://localhost:8080}

echo "=========================================="
echo "Eliminando reglas generadas automáticamente"
echo "=========================================="
echo ""
echo "Backend URL: $BACKEND_URL"
echo ""

response=$(curl -s -X DELETE "${BACKEND_URL}/rulesets/auto-generated")

if [ $? -eq 0 ]; then
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    echo ""
    echo "✅ Completado"
else
    echo "❌ Error al conectar con el backend"
    echo "💡 Verifica que el backend esté corriendo en $BACKEND_URL"
    exit 1
fi

