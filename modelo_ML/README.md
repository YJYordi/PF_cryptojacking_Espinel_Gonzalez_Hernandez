# Sistema de Detección de Cryptojacking con ML

Sistema automatizado de detección de cryptojacking que integra Machine Learning, Suricata y OpenAI para generar reglas automáticas.

## 📁 Estructura del Proyecto

```
modelo_ML/
├── data/                           # Datos y datasets
│   └── dataset.csv                # Dataset de entrenamiento
├── models/                         # Modelos entrenados
│   ├── rf_model.pkl               # Random Forest (supervisado)
│   ├── iso_model.pkl              # Isolation Forest (no supervisado)
│   └── scaler.pkl                 # Normalizador de datos
├── scripts/                        # Scripts de utilidad
│   ├── generate_data.py           # Recolector de datos del sistema
│   └── generate_synthetic_dataset.py  # Generador de dataset sintético
├── detect.py                       # Detector en tiempo real
├── train_model.py                  # Entrenamiento de modelos
├── pipeline_monitor.py             # Pipeline automatizado completo ⭐
├── generate_suricata_rules.py      # Generador de reglas (standalone)
├── requirements.txt                # Dependencias Python
├── .gitignore                      # Archivos a ignorar en Git
└── README.md                       # Este archivo
```

## 🚀 Inicio Rápido

### Opción 1: Con Docker (Recomendado)

El sistema ML se integra automáticamente con Docker Compose:

```bash
# 1. Agregar OPENAI_API_KEY al .env del backend
cd ../PF_backend/ProyectoFinal_Backend
echo "OPENAI_API_KEY=tu-api-key" >> .env

# 2. Entrenar modelos (si no existen)
cd ../../modelo_ML
python scripts/generate_synthetic_dataset.py
python train_model.py

# 3. Levantar todos los servicios (incluye ML)
cd ../PF_backend/ProyectoFinal_Backend
docker compose up --build
```

El servicio `ml-pipeline` se iniciará automáticamente y estará en escucha.

### Opción 2: Sin Docker

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Generar Dataset (si no existe)

```bash
python scripts/generate_synthetic_dataset.py
```

### 3. Entrenar Modelos

```bash
python train_model.py
```

### 4. Ejecutar Pipeline Automatizado

```bash
export OPENAI_API_KEY="tu-api-key"
python pipeline_monitor.py
```

## 📋 Scripts Principales

### `pipeline_monitor.py` - Pipeline Automatizado
**Propósito**: Monitoreo continuo y generación automática de reglas

**Funcionalidad**:
- Monitorea métricas del sistema cada 10 segundos
- Detecta minería sospechosa con modelo ML
- Verifica si Suricata ya tiene alertas
- Solo genera reglas si Suricata NO detectó la amenaza
- Envía reglas automáticamente al backend
- Las reglas aparecen en el Dashboard

**Uso**:
```bash
python pipeline_monitor.py --backend-url http://localhost:8080
```

### `detect.py` - Detector en Tiempo Real
**Propósito**: Detección puntual de cryptojacking

**Uso**:
```bash
python detect.py
```

O desde código:
```python
from detect import CryptojackingDetector
detector = CryptojackingDetector()
result = detector.get_prediction()
```

### `train_model.py` - Entrenamiento
**Propósito**: Entrenar modelos de ML

**Uso**:
```bash
python train_model.py
```

### `scripts/generate_data.py` - Recolector de Datos
**Propósito**: Recolectar datos reales del sistema para entrenamiento

**Uso**:
```bash
python scripts/generate_data.py normal    # Etiqueta: 0
python scripts/generate_data.py minado   # Etiqueta: 1
```

### `scripts/generate_synthetic_dataset.py` - Dataset Sintético
**Propósito**: Generar dataset sintético pero realista

**Uso**:
```bash
python scripts/generate_synthetic_dataset.py
```

### `generate_suricata_rules.py` - Generador de Reglas (Standalone)
**Propósito**: Generar reglas desde eve.json sin pipeline completo

**Uso**:
```bash
python generate_suricata_rules.py --ip 192.168.1.50 --input eve.json --apply
```

## 🔧 Configuración

### Variables de Entorno

```bash
export OPENAI_API_KEY="tu-api-key-de-openai"
```

### Configuración del Pipeline

Edita `pipeline_monitor.py` para ajustar:
- `DEFAULT_EVE_JSON`: Ruta al archivo eve.json de Suricata
- `DEFAULT_BACKEND_URL`: URL del backend
- `INTERVAL_SECONDS`: Intervalo de monitoreo

## 🔄 Flujo del Sistema

```
1. Pipeline monitorea sistema (cada 10s)
   ↓
2. Modelo ML detecta minería sospechosa
   ↓
3. Verifica si Suricata ya tiene alertas
   ↓
4. Si Suricata NO detectó:
   - Lee eve.json
   - Envía a OpenAI
   - Genera reglas
   - Envía al backend
   - Aparece en Dashboard
```

## 📊 Modelos

- **Random Forest**: Modelo supervisado (99.55% accuracy)
- **Isolation Forest**: Modelo no supervisado (solo datos normales)

## 🎯 Características

- ✅ Detección en tiempo real
- ✅ Generación automática de reglas
- ✅ Integración con backend y dashboard
- ✅ Optimización: solo genera reglas si Suricata no detectó
- ✅ Pipeline completamente automatizado

## 📝 Notas

- Los modelos se guardan en `models/`
- Los datasets se guardan en `data/`
- Las reglas generadas se envían automáticamente al backend
- El Dashboard se actualiza automáticamente con nuevas reglas

