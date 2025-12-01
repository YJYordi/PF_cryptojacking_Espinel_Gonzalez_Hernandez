#!/usr/bin/env python3
"""
Genera un dataset sintético pero realista para entrenar el modelo de detección de cryptojacking.
Simula comportamientos de sistema normal, con carga legítima, y con XMRig minando.
"""

import pandas as pd  # type: ignore
import numpy as np
import random
from datetime import datetime, timedelta
import csv

# Configuración
import os
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATASET_FILE = os.path.join(DATA_DIR, "dataset.csv")

# Configuración de red (entorno del lab)
POOL_IP = "192.168.100.30"
VICTIM_IP = "192.168.100.10"

# Cantidad de muestras recomendadas para buen entrenamiento:
# - Normal: 1000-1500 (comportamiento base del sistema)
# - Carga legítima: 300-500 (evitar falsos positivos)
# - Minería: 800-1200 (clase de interés, MÁS muestras para aprender patrones reales)
# Total recomendado: 2100-3200 muestras
SAMPLES_NORMAL = 1200     # Muestras de comportamiento normal
SAMPLES_LOAD = 400        # Muestras de carga legítima (compilación, video, etc.)
SAMPLES_MINING = 1000     # Muestras de minería con XMRig (AUMENTADO para mejor aprendizaje)

# Semilla para reproducibilidad
np.random.seed(42)
random.seed(42)


def generate_normal_sample(timestamp):
    """
    Genera una muestra de comportamiento normal del sistema con variabilidad realista.
    Características:
    - CPU: 5-60% (uso normal con variabilidad)
    - RAM: 25-70% (uso normal con variabilidad)
    - Red: Tráfico variable y esporádico con ruido
    - Procesos: Cantidad normal, sin xmrig (pero con casos límite)
    """
    # CPU con más variabilidad y casos límite ocasionales
    if random.random() < 0.1:  # 10% de casos con CPU más alto (actividad intensa momentánea)
        cpu = np.random.normal(45, 15)
        cpu = max(30, min(70, cpu))
    else:
        cpu = np.random.normal(25, 15)  # Mayor desviación estándar
        cpu = max(5, min(60, cpu))
    
    # RAM con variabilidad natural
    ram = np.random.normal(45, 15)  # Mayor variabilidad
    ram = max(25, min(70, ram))
    
    # Tráfico de red variable con más ruido
    if random.random() < 0.25:  # 25% de probabilidad de pico
        bytes_sent = np.random.exponential(60000) + np.random.normal(0, 10000)
        bytes_recv = np.random.exponential(120000) + np.random.normal(0, 20000)
    elif random.random() < 0.1:  # 10% de casos con tráfico muy bajo
        bytes_sent = max(0, int(np.random.exponential(1000)))
        bytes_recv = max(0, int(np.random.exponential(2000)))
    else:
        bytes_sent = np.random.exponential(8000) + np.random.normal(0, 3000)
        bytes_recv = np.random.exponential(15000) + np.random.normal(0, 5000)
    
    bytes_sent = max(0, int(bytes_sent))
    bytes_recv = max(0, int(bytes_recv))
    
    # Cantidad de procesos con variabilidad
    process_count = random.randint(70, 160)
    
    # Sin xmrig (pero ocasionalmente puede haber procesos con nombres similares)
    xmrig_detected = 0
    
    # Lista de procesos simulada (Windows, sin xmrig) con más variabilidad
    processes = [
        f"chrome.exe:{random.uniform(0, 8):.1f}:{random.uniform(0.5, 4):.1f}",
        f"Code.exe:{random.uniform(0, 5):.1f}:{random.uniform(0.8, 3):.1f}",
        f"node.exe:{random.uniform(0, 4):.1f}:{random.uniform(0.3, 2):.1f}",
        f"explorer.exe:{random.uniform(0, 2):.1f}:{random.uniform(0.2, 1.2):.1f}",
        f"svchost.exe:{random.uniform(0, 1):.1f}:{random.uniform(0.1, 0.8):.1f}",
    ]
    
    # Ocasionalmente agregar procesos adicionales
    if random.random() < 0.3:
        processes.append(f"steam.exe:{random.uniform(0, 3):.1f}:{random.uniform(0.5, 2):.1f}")
    if random.random() < 0.2:
        processes.append(f"discord.exe:{random.uniform(0, 2):.1f}:{random.uniform(0.3, 1.5):.1f}")
    
    process_list = "|".join(processes)
    
    return {
        'timestamp': timestamp,
        'cpu_percent': round(cpu, 2),
        'ram_percent': round(ram, 2),
        'bytes_sent': bytes_sent,
        'bytes_recv': bytes_recv,
        'process_count': process_count,
        'process_list': process_list,
        'xmrig_detected': xmrig_detected,
        'label': 0
    }


def generate_load_sample(timestamp):
    """
    Genera una muestra de carga legítima alta con variabilidad realista.
    Características:
    - CPU: 45-90% (carga alta pero legítima, con solapamiento)
    - RAM: 35-80% (uso alto con variabilidad)
    - Red: Tráfico variable, puede ser alto o bajo
    - Procesos: Sin xmrig, pero con procesos intensivos
    """
    # CPU con más variabilidad y solapamiento con minería
    cpu = np.random.normal(65, 20)  # Mayor desviación
    cpu = max(45, min(90, cpu))  # Solapamiento con minería (80-90%)
    
    ram = np.random.normal(55, 18)  # Mayor variabilidad
    ram = max(35, min(80, ram))
    
    # Tráfico de red variable con más ruido
    if random.random() < 0.4:  # 40% de probabilidad de tráfico alto
        bytes_sent = np.random.exponential(100000) + np.random.normal(0, 20000)
        bytes_recv = np.random.exponential(250000) + np.random.normal(0, 40000)
    elif random.random() < 0.3:  # 30% de tráfico medio
        bytes_sent = np.random.exponential(40000) + np.random.normal(0, 10000)
        bytes_recv = np.random.exponential(80000) + np.random.normal(0, 15000)
    else:  # 30% de tráfico bajo (compilación local)
        bytes_sent = np.random.exponential(15000) + np.random.normal(0, 5000)
        bytes_recv = np.random.exponential(30000) + np.random.normal(0, 8000)
    
    bytes_sent = max(0, int(bytes_sent))
    bytes_recv = max(0, int(bytes_recv))
    
    # Más procesos por carga
    process_count = random.randint(110, 190)
    
    # Sin xmrig
    xmrig_detected = 0
    
    # Procesos intensivos pero legítimos (Windows) con variabilidad
    processes = [
        f"msbuild.exe:{random.uniform(8, 35):.1f}:{random.uniform(1.5, 6):.1f}",
        f"cl.exe:{random.uniform(3, 18):.1f}:{random.uniform(0.8, 4):.1f}",
        f"ffmpeg.exe:{random.uniform(12, 45):.1f}:{random.uniform(2.5, 10):.1f}",
        f"chrome.exe:{random.uniform(1, 10):.1f}:{random.uniform(0.8, 5):.1f}",
        f"Code.exe:{random.uniform(0.5, 6):.1f}:{random.uniform(0.3, 3):.1f}",
    ]
    
    # Ocasionalmente agregar otros procesos
    if random.random() < 0.4:
        processes.append(f"python.exe:{random.uniform(2, 15):.1f}:{random.uniform(0.5, 3):.1f}")
    
    process_list = "|".join(processes)
    
    return {
        'timestamp': timestamp,
        'cpu_percent': round(cpu, 2),
        'ram_percent': round(ram, 2),
        'bytes_sent': bytes_sent,
        'bytes_recv': bytes_recv,
        'process_count': process_count,
        'process_list': process_list,
        'xmrig_detected': xmrig_detected,
        'label': 0  # También es "normal" pero con carga
    }


def generate_mining_sample(timestamp):
    """
    Genera una muestra de minería con XMRig con variabilidad realista.
    Características REALES basadas en observaciones:
    - CPU: 80-100% (típicamente 90-100% cuando está minando activamente)
    - RAM: 20-85% (puede variar mucho, especialmente si hay otros procesos)
    - Red: Tráfico moderado-alto (comunicación constante con pool)
    - Procesos: xmrig presente, pero ocasionalmente puede no detectarse
    """
    # CPU: La mayoría del tiempo está muy alto (85-100%)
    # Casos reales: CPU puede estar al 100% cuando mina activamente
    # IMPORTANTE: Más casos con CPU 95-100% para que el modelo aprenda
    if random.random() < 0.08:  # 8% de casos con CPU más bajo (inicio, pausa, throttling)
        cpu = np.random.normal(82, 6)
        cpu = max(75, min(90, cpu))
    elif random.random() < 0.35:  # 35% de casos con CPU muy alto (95-100%) - AUMENTADO
        cpu = np.random.normal(98, 1.5)
        cpu = max(95, min(100, cpu))
    else:  # 57% de casos: CPU alto pero variable (85-98%)
        cpu = np.random.normal(92, 4)
        cpu = max(85, min(100, cpu))
    
    # RAM: Puede variar mucho dependiendo del sistema
    # Casos reales: RAM puede estar alta (60-90%) si hay otros procesos
    # IMPORTANTE: Más casos con RAM alta (70-90%) para casos como el observado
    if random.random() < 0.25:  # 25% de casos con RAM muy alta (80-90%) - casos extremos
        ram = np.random.normal(83, 5)
        ram = max(75, min(90, ram))
    elif random.random() < 0.30:  # 30% de casos con RAM alta (60-80%) - otros procesos activos
        ram = np.random.normal(70, 8)
        ram = max(60, min(85, ram))
    else:  # 45% de casos: RAM moderada (20-60%) - solo XMRig o pocos procesos
        ram = np.random.normal(40, 15)
        ram = max(20, min(65, ram))
    
    # Tráfico de red: XMRig mantiene comunicación constante con el pool
    # Tráfico típico: moderado-alto, con picos cuando envía shares
    if random.random() < 0.25:  # 25% de picos de tráfico (enviando shares)
        bytes_sent = np.random.normal(45000, 15000)
        bytes_recv = np.random.normal(60000, 20000)
    elif random.random() < 0.1:  # 10% de tráfico muy bajo (esperando work, inicio)
        bytes_sent = max(0, int(np.random.normal(3000, 1500)))
        bytes_recv = max(0, int(np.random.normal(8000, 3000)))
    else:  # 65% tráfico normal-alto (comunicación constante con pool)
        bytes_sent = np.random.normal(25000, 10000)
        bytes_recv = np.random.normal(40000, 15000)
    
    bytes_sent = max(0, int(bytes_sent))
    bytes_recv = max(0, int(bytes_recv))
    
    # Cantidad de procesos: puede variar, pero típicamente más procesos cuando hay minería
    process_count = random.randint(90, 180)
    
    # XMRig detectado (pero ocasionalmente puede no detectarse - casos límite)
    if random.random() < 0.08:  # 8% de casos donde xmrig no se detecta (proceso oculto, nombre diferente)
        xmrig_detected = 0
    else:
        xmrig_detected = 1
    
    # Procesos con xmrig usando CPU variable (típicamente muy alto)
    if xmrig_detected == 1:
        # XMRig típicamente usa 70-100% de CPU cuando está activo
        xmrig_cpu = random.uniform(75, 100)  # Mayor rango, más realista
        xmrig_mem = random.uniform(0.5, 3.0)  # XMRig puede usar más RAM en algunos casos
        processes = [
            f"xmrig.exe:{xmrig_cpu:.1f}:{xmrig_mem:.1f}",
            f"chrome.exe:{random.uniform(0, 5):.1f}:{random.uniform(0.8, 3):.1f}",
            f"svchost.exe:{random.uniform(0, 1.5):.1f}:{random.uniform(0.1, 0.8):.1f}",
            f"explorer.exe:{random.uniform(0, 1):.1f}:{random.uniform(0.2, 1):.1f}",
        ]
    else:
        # Caso donde xmrig existe pero no se detecta (proceso con nombre diferente o oculto)
        processes = [
            f"miner.exe:{random.uniform(70, 95):.1f}:{random.uniform(0.3, 2):.1f}",  # Nombre diferente
            f"chrome.exe:{random.uniform(0, 3):.1f}:{random.uniform(1, 2):.1f}",
            f"svchost.exe:{random.uniform(0, 1):.1f}:{random.uniform(0.1, 0.5):.1f}",
        ]
    
    process_list = "|".join(processes)
    
    return {
        'timestamp': timestamp,
        'cpu_percent': round(cpu, 2),
        'ram_percent': round(ram, 2),
        'bytes_sent': bytes_sent,
        'bytes_recv': bytes_recv,
        'process_count': process_count,
        'process_list': process_list,
        'xmrig_detected': xmrig_detected,
        'label': 1  # Minería
    }


def generate_dataset():
    """Genera el dataset completo con todas las muestras."""
    print("=" * 60)
    print("GENERADOR DE DATASET SINTÉTICO")
    print("=" * 60)
    print(f"[INFO] Entorno: Windows")
    print(f"[INFO] IP Víctima: {VICTIM_IP}")
    print(f"[INFO] IP Pool: {POOL_IP}")
    print(f"[INFO] Generando {SAMPLES_NORMAL} muestras normales")
    print(f"[INFO] Generando {SAMPLES_LOAD} muestras de carga legítima")
    print(f"[INFO] Generando {SAMPLES_MINING} muestras de minería")
    print(f"[INFO] Total: {SAMPLES_NORMAL + SAMPLES_LOAD + SAMPLES_MINING} muestras")
    print("=" * 60)
    
    # Columnas del dataset
    columns = [
        "timestamp",
        "cpu_percent",
        "ram_percent",
        "bytes_sent",
        "bytes_recv",
        "process_count",
        "process_list",
        "xmrig_detected",
        "label"
    ]
    
    # Generar timestamp base
    base_time = datetime.now() - timedelta(days=7)
    
    samples = []
    
    # Generar muestras normales
    print("\n[1/3] Generando muestras normales...")
    for i in range(SAMPLES_NORMAL):
        timestamp = base_time + timedelta(seconds=i * 10)  # Cada 10 segundos
        sample = generate_normal_sample(timestamp.isoformat())
        samples.append(sample)
        if (i + 1) % 100 == 0:
            print(f"  Progreso: {i + 1}/{SAMPLES_NORMAL}")
    
    # Generar muestras de carga
    print(f"\n[2/3] Generando muestras de carga legítima...")
    for i in range(SAMPLES_LOAD):
        timestamp = base_time + timedelta(seconds=(SAMPLES_NORMAL + i) * 10)
        sample = generate_load_sample(timestamp.isoformat())
        samples.append(sample)
        if (i + 1) % 50 == 0:
            print(f"  Progreso: {i + 1}/{SAMPLES_LOAD}")
    
    # Generar muestras de minería
    print(f"\n[3/3] Generando muestras de minería...")
    for i in range(SAMPLES_MINING):
        timestamp = base_time + timedelta(seconds=(SAMPLES_NORMAL + SAMPLES_LOAD + i) * 10)
        sample = generate_mining_sample(timestamp.isoformat())
        samples.append(sample)
        if (i + 1) % 50 == 0:
            print(f"  Progreso: {i + 1}/{SAMPLES_MINING}")
    
    # Mezclar las muestras para que no estén ordenadas
    print("\n[INFO] Mezclando muestras...")
    random.shuffle(samples)
    
    # Crear DataFrame y guardar
    print("\n[INFO] Guardando dataset...")
    df = pd.DataFrame(samples)
    df = df[columns]  # Asegurar orden de columnas
    
    df.to_csv(DATASET_FILE, index=False)
    
    # Estadísticas
    print("\n" + "=" * 60)
    print("ESTADÍSTICAS DEL DATASET")
    print("=" * 60)
    print(f"Total de muestras: {len(df)}")
    print(f"\nDistribución por label:")
    print(df['label'].value_counts())
    print(f"\nDistribución por xmrig_detected:")
    print(df['xmrig_detected'].value_counts())
    print(f"\nEstadísticas de CPU:")
    print(df.groupby('label')['cpu_percent'].describe())
    print(f"\nEstadísticas de RAM:")
    print(df.groupby('label')['ram_percent'].describe())
    print(f"\nEstadísticas de Red (bytes_sent):")
    print(df.groupby('label')['bytes_sent'].describe())
    print("=" * 60)
    print(f"\n[INFO] Dataset guardado en: {DATASET_FILE}")
    print("[INFO] Listo para entrenar el modelo con: python train_model.py")


if __name__ == "__main__":
    generate_dataset()

