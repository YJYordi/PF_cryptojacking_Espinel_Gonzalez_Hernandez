"""
Script de entrenamiento para modelos de detección de cryptojacking.
Entrena Random Forest (supervisado) e Isolation Forest (no supervisado).
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pickle
import os

# Rutas de archivos
DATA_DIR = "data"
MODELS_DIR = "models"
DATASET_FILE = os.path.join(DATA_DIR, "dataset.csv")
RF_MODEL_FILE = os.path.join(MODELS_DIR, "rf_model.pkl")
ISO_MODEL_FILE = os.path.join(MODELS_DIR, "iso_model.pkl")
SCALER_FILE = os.path.join(MODELS_DIR, "scaler.pkl")

def load_dataset(filepath):
    """Carga el dataset desde CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"El archivo {filepath} no existe.")
    
    df = pd.read_csv(filepath)
    print(f"[INFO] Dataset cargado: {len(df)} filas, {len(df.columns)} columnas")
    return df

def preprocess_data(df):
    """
    Preprocesa los datos:
    - Reemplaza valores faltantes
    - Normaliza variables numéricas
    - Codifica columnas categóricas si existen
    """
    df = df.copy()
    
    # Eliminar columnas no útiles para el modelo
    columns_to_drop = ['timestamp', 'process_list']
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
    
    # Reemplazar valores faltantes en columnas numéricas con la mediana
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isna().any():
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            print(f"[INFO] Valores faltantes en '{col}' reemplazados con mediana: {median_val}")
    
    # Codificar xmrig_detected si es necesario (ya debería ser numérico)
    if 'xmrig_detected' in df.columns:
        if df['xmrig_detected'].dtype == 'object':
            df['xmrig_detected'] = df['xmrig_detected'].astype(int)
    
    # Separar features y label
    if 'label' not in df.columns:
        raise ValueError("La columna 'label' no existe en el dataset.")
    
    X = df.drop(columns=['label'])
    y = df['label']
    
    # Normalizar variables numéricas
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
    
    print(f"[INFO] Preprocesamiento completado. Features: {X_scaled.shape[1]}")
    return X_scaled, y, scaler

def train_random_forest(X, y):
    """Entrena un modelo Random Forest y muestra métricas."""
    print("\n[INFO] Entrenando Random Forest...")
    
    # Separar en train y test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Entrenar modelo
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    
    # Predicciones
    y_pred = rf_model.predict(X_test)
    y_pred_proba = rf_model.predict_proba(X_test)[:, 1]
    
    # Métricas
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    print("\n[RESULTADOS] Random Forest:")
    print(f"  Accuracy:  {accuracy:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    
    return rf_model

def train_isolation_forest(X, y):
    """
    Entrena Isolation Forest SOLO con datos etiquetados como 'normal' (label=0).
    """
    print("\n[INFO] Entrenando Isolation Forest con datos normales...")
    
    # Filtrar solo datos normales
    X_normal = X[y == 0]
    
    if len(X_normal) == 0:
        raise ValueError("No hay datos etiquetados como 'normal' (label=0) en el dataset.")
    
    print(f"[INFO] Usando {len(X_normal)} muestras normales para entrenar Isolation Forest")
    
    # Entrenar modelo
    iso_model = IsolationForest(
        contamination=0.1,  # Esperamos ~10% de anomalías
        random_state=42,
        n_jobs=-1
    )
    iso_model.fit(X_normal)
    
    print("[INFO] Isolation Forest entrenado exitosamente")
    
    return iso_model

def save_models(rf_model, iso_model, scaler):
    """Guarda los modelos y el scaler en archivos pickle."""
    with open(RF_MODEL_FILE, 'wb') as f:
        pickle.dump(rf_model, f)
    print(f"[INFO] Random Forest guardado en {RF_MODEL_FILE}")
    
    with open(ISO_MODEL_FILE, 'wb') as f:
        pickle.dump(iso_model, f)
    print(f"[INFO] Isolation Forest guardado en {ISO_MODEL_FILE}")
    
    with open(SCALER_FILE, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"[INFO] Scaler guardado en {SCALER_FILE}")

def main():
    """Función principal."""
    print("=" * 60)
    print("ENTRENAMIENTO DE MODELOS DE DETECCIÓN DE CRYPTOJACKING")
    print("=" * 60)
    
    # 1. Cargar dataset
    df = load_dataset(DATASET_FILE)
    
    # 2. Preprocesamiento
    X, y, scaler = preprocess_data(df)
    
    # 3. Entrenar Random Forest
    rf_model = train_random_forest(X, y)
    
    # 4. Entrenar Isolation Forest (solo con datos normales)
    iso_model = train_isolation_forest(X, y)
    
    # 5. Guardar modelos
    save_models(rf_model, iso_model, scaler)
    
    print("\n[INFO] Entrenamiento completado exitosamente!")

if __name__ == "__main__":
    main()

