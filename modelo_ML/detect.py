"""
Script de inferencia para detección de cryptojacking en tiempo real.
Carga el modelo entrenado y predice si el sistema muestra comportamiento de minado.
"""

import psutil
import pickle
import os
import numpy as np
import pandas as pd
from datetime import datetime

# Rutas de archivos
MODELS_DIR = "models"
RF_MODEL_FILE = os.path.join(MODELS_DIR, "rf_model.pkl")
SCALER_FILE = os.path.join(MODELS_DIR, "scaler.pkl")

class CryptojackingDetector:
    """Clase para detectar cryptojacking usando modelos entrenados."""
    
    def __init__(self, model_path=RF_MODEL_FILE, scaler_path=SCALER_FILE):
        """Inicializa el detector cargando el modelo y el scaler."""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"El modelo {model_path} no existe. Ejecuta train_model.py primero.")
        
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"El scaler {scaler_path} no existe. Ejecuta train_model.py primero.")
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        # Estado previo para calcular diferencias de red
        self.prev_net = None
        
        print(f"[INFO] Modelo cargado desde {model_path}")
        print(f"[INFO] Scaler cargado desde {scaler_path}")
    
    def collect_metrics(self):
        """
        Recolecta las mismas métricas que generate_data.py:
        - cpu_percent
        - ram_percent
        - bytes_sent (diferencia desde última medición)
        - bytes_recv (diferencia desde última medición)
        - process_count
        - xmrig_detected
        """
        # CPU y RAM
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram_percent = psutil.virtual_memory().percent
        
        # Red (bytes enviados y recibidos como diferencia)
        net = psutil.net_io_counters()
        if self.prev_net is None:
            # Primera vez: usar valores absolutos como aproximación
            bytes_sent = net.bytes_sent
            bytes_recv = net.bytes_recv
        else:
            # Calcular diferencia como en generate_data.py
            bytes_sent = net.bytes_sent - self.prev_net.bytes_sent
            bytes_recv = net.bytes_recv - self.prev_net.bytes_recv
        
        self.prev_net = net
        
        # Procesos activos
        procesos = []
        xmrig_detected = False
        
        for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
            try:
                name = p.info["name"] or "unknown"
                procesos.append(name)
                
                if "xmrig" in name.lower():
                    xmrig_detected = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        process_count = len(procesos)
        
        # Crear diccionario con las métricas
        metrics = {
            "cpu_percent": cpu_percent,
            "ram_percent": ram_percent,
            "bytes_sent": bytes_sent,
            "bytes_recv": bytes_recv,
            "process_count": process_count,
            "xmrig_detected": int(xmrig_detected)
        }
        
        return metrics
    
    def preprocess_sample(self, metrics_dict):
        """
        Preprocesa una muestra individual:
        - Convierte a DataFrame
        - Normaliza usando el scaler entrenado
        - Mantiene el orden de columnas consistente
        """
        # Orden esperado de columnas (sin timestamp, process_list, label)
        expected_columns = ['cpu_percent', 'ram_percent', 'bytes_sent', 
                          'bytes_recv', 'process_count', 'xmrig_detected']
        
        # Crear DataFrame con una sola fila, asegurando el orden correcto
        df = pd.DataFrame([metrics_dict])
        
        # Eliminar columnas que no se usan en el modelo
        columns_to_drop = ['timestamp', 'process_list', 'label']
        df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
        
        # Reordenar columnas según el orden esperado (si existen)
        available_columns = [col for col in expected_columns if col in df.columns]
        df = df[available_columns]
        
        # Normalizar
        X_scaled = self.scaler.transform(df)
        X_scaled = pd.DataFrame(X_scaled, columns=df.columns)
        
        return X_scaled
    
    def predict(self, metrics_dict=None):
        """
        Predice si hay cryptojacking basado en las métricas del sistema.
        
        Args:
            metrics_dict: Diccionario con métricas. Si es None, las recolecta automáticamente.
        
        Returns:
            dict: {
                'prediction': 0 (normal) o 1 (malicious),
                'probability': probabilidad de ser malicious,
                'class': 'normal' o 'malicious',
                'metrics': métricas usadas
            }
        """
        if metrics_dict is None:
            metrics_dict = self.collect_metrics()
        
        # Preprocesar
        X_scaled = self.preprocess_sample(metrics_dict)
        
        # Predecir
        prediction = self.model.predict(X_scaled)[0]
        probability = self.model.predict_proba(X_scaled)[0, 1]  # Probabilidad de clase 1 (malicious)
        
        result = {
            'prediction': int(prediction),
            'probability': float(probability),
            'class': 'malicious' if prediction == 1 else 'normal',
            'metrics': metrics_dict
        }
        
        return result
    
    def get_prediction(self, metrics_dict=None):
        """
        Función exportable para ser consumida por otros sistemas.
        Retorna un diccionario con la predicción y probabilidad.
        
        Args:
            metrics_dict: Diccionario opcional con métricas. Si es None, las recolecta.
        
        Returns:
            dict: {
                'is_malicious': bool,
                'probability': float (0-1),
                'class': str ('normal' o 'malicious'),
                'timestamp': str (ISO format)
            }
        """
        result = self.predict(metrics_dict)
        
        return {
            'is_malicious': result['prediction'] == 1,
            'probability': result['probability'],
            'class': result['class'],
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Función principal para ejecutar detección desde consola."""
    print("=" * 60)
    print("DETECTOR DE CRYPTOJACKING")
    print("=" * 60)
    
    try:
        # Inicializar detector
        detector = CryptojackingDetector()
        
        # Recolectar métricas y predecir
        print("\n[INFO] Recolectando métricas del sistema...")
        result = detector.predict()
        
        # Mostrar resultados
        print("\n[RESULTADO]")
        print(f"  Clase predicha: {result['class'].upper()}")
        print(f"  Probabilidad de cryptojacking: {result['probability']:.4f} ({result['probability']*100:.2f}%)")
        print(f"\n[MÉTRICAS]")
        print(f"  CPU: {result['metrics']['cpu_percent']:.2f}%")
        print(f"  RAM: {result['metrics']['ram_percent']:.2f}%")
        print(f"  Procesos: {result['metrics']['process_count']}")
        print(f"  XMRig detectado: {'Sí' if result['metrics']['xmrig_detected'] else 'No'}")
        
        if result['prediction'] == 1:
            print("\n[ALERTA] ⚠️  Se detectó posible comportamiento de cryptojacking!")
        else:
            print("\n[OK] ✓ Sistema operando normalmente")
        
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        print("[INFO] Ejecuta train_model.py primero para entrenar los modelos.")
    except Exception as e:
        print(f"[ERROR] Error durante la detección: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

