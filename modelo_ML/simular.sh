#!/bin/bash
# Script único para simular actividad sospechosa dentro del contenedor
# Permite simular tanto tráfico de red como carga de CPU/RAM

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
DURATION=${DURATION:-30}
TARGET_IP=${TARGET_IP:-192.168.100.30}
TARGET_PORT=${TARGET_PORT:-8080}

show_help() {
    echo "=========================================="
    echo "SIMULADOR DE ACTIVIDAD SOSPECHOSA"
    echo "=========================================="
    echo ""
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  --network, -n     Simular tráfico de red (HTTP/TCP)"
    echo "  --cpu, -c          Simular carga de CPU/RAM"
    echo "  --both, -b         Simular ambos (red + CPU)"
    echo "  --duration, -d N   Duración en segundos (default: 30)"
    echo "  --help, -h         Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 --network              # Solo tráfico de red"
    echo "  $0 --cpu                  # Solo carga de CPU"
    echo "  $0 --both                 # Ambos simultáneamente"
    echo "  $0 --network --duration 60 # Red durante 60 segundos"
    echo ""
}

simulate_network() {
    local duration=$1
    local target_ip=$2
    local target_port=$3
    
    echo -e "${BLUE}[INFO]${NC} Simulando tráfico de red..."
    echo -e "  Target: ${target_ip}:${target_port}"
    echo -e "  Duración: ${duration} segundos"
    echo ""
    
    docker compose exec ml-pipeline python3 -c "
import time
import socket
import random

target_ip = '${target_ip}'
target_port = ${target_port}
duration = ${duration}
start_time = time.time()
connection_count = 0

print('Iniciando simulación de tráfico de red...')
while time.time() - start_time < duration:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect((target_ip, target_port))
            connection_count += 1
            
            # Enviar más datos para generar más tráfico
            data = b'X' * random.randint(1000, 5000)  # Más datos
            sock.send(data)
            # Enviar múltiples veces
            for _ in range(3):
                sock.send(b'Y' * random.randint(500, 2000))
            
            # Intentar recibir
            try:
                sock.recv(1024)
            except socket.timeout:
                pass
            
            sock.close()
        except (socket.error, OSError):
            pass
        time.sleep(0.1)
    except Exception as e:
        time.sleep(0.5)

print(f'Simulación completada: {connection_count} conexiones')
"
}

simulate_cpu() {
    local duration=$1
    
    echo -e "${BLUE}[INFO]${NC} Simulando carga de CPU y RAM al 90%..."
    echo -e "  Duración: ${duration} segundos"
    echo -e "  ${YELLOW}OBJETIVO:${NC} CPU ~90% | RAM ~90%"
    echo ""
    
    docker compose exec ml-pipeline python3 -c "
import multiprocessing
import time
import sys

# Función para carga intensa de CPU
def cpu_load(_):
    while True:
        # Cálculos muy pesados para saturar CPU
        result = sum(i**3 for i in range(10000))
        result = sum(i*i for i in range(15000))
        result = sum(i**2.5 for i in range(8000))
        # Más cálculos
        for _ in range(100):
            x = sum(i for i in range(5000))

# Función para consumir RAM
def ram_load(target_mb):
    # Consumir RAM específica por proceso
    data = []
    bytes_per_mb = 1024 * 1024
    target_bytes = target_mb * bytes_per_mb
    
    # Llenar lista con datos para consumir RAM
    chunk_size = 100000  # ~800KB por chunk
    while sys.getsizeof(data) < target_bytes:
        data.extend([0] * chunk_size)
        # Pequeña pausa para no bloquear
        if len(data) % (chunk_size * 10) == 0:
            time.sleep(0.001)
    
    # Mantener los datos en memoria
    while True:
        time.sleep(1)
        # Acceder a los datos para mantenerlos en RAM
        _ = sum(data[:1000])

duration = ${duration}
print('Iniciando carga intensa de CPU y RAM...')
print('  Objetivo: CPU ~90% | RAM ~90%')
print('')

# Obtener número de CPUs y RAM disponibles
import os
import psutil

num_cpus = os.cpu_count() or 4
mem = psutil.virtual_memory()
total_ram_gb = mem.total / (1024**3)
available_ram_gb = mem.available / (1024**3)

print(f'  CPUs disponibles: {num_cpus}')
print(f'  RAM total: {total_ram_gb:.2f} GB')
print(f'  RAM disponible: {available_ram_gb:.2f} GB')

# Calcular RAM objetivo (90% del total)
target_ram_percent = 0.90
# Calcular cuánta RAM necesitamos consumir (90% del total menos la ya usada)
current_ram_used_gb = (mem.total - mem.available) / (1024**3)
target_ram_used_gb = total_ram_gb * target_ram_percent
ram_to_consume_gb = max(0, target_ram_used_gb - current_ram_used_gb)
ram_to_consume_mb = ram_to_consume_gb * 1024

# Crear procesos para CPU (usar todos los cores para saturar)
cpu_processes = num_cpus
print(f'  Procesos de CPU: {cpu_processes} (saturará todos los cores)')

# Crear procesos para RAM (distribuir la carga)
# Cada proceso consumirá ~200-300MB
if ram_to_consume_mb > 0:
    ram_processes = max(2, min(6, int(ram_to_consume_mb / 250)))  # 2-6 procesos
    ram_per_process_mb = max(200, int(ram_to_consume_mb / ram_processes))
else:
    ram_processes = 2
    ram_per_process_mb = 300  # Consumir algo de RAM de todas formas

print(f'  RAM actual usada: {current_ram_used_gb:.2f} GB')
print(f'  RAM objetivo: {target_ram_used_gb:.2f} GB ({target_ram_percent*100:.0f}%)')
print(f'  RAM a consumir: {ram_to_consume_mb:.0f} MB')
print(f'  Procesos de RAM: {ram_processes}')
print(f'  RAM por proceso: ~{ram_per_process_mb} MB')
print('')

# Pool para CPU
cpu_pool = multiprocessing.Pool(cpu_processes)

# Procesos para RAM
ram_procs = []
for i in range(ram_processes):
    p = multiprocessing.Process(target=ram_load, args=(ram_per_process_mb,))
    p.start()
    ram_procs.append(p)
    time.sleep(0.1)  # Pequeña pausa entre procesos

# Ejecutar carga de CPU
start_time = time.time()
try:
    while time.time() - start_time < duration:
        # Ejecutar carga de CPU intensa
        cpu_pool.map(cpu_load, range(cpu_processes))
        elapsed = int(time.time() - start_time)
        if elapsed % 5 == 0 and elapsed > 0:
            # Mostrar métricas actuales
            current_mem = psutil.virtual_memory()
            current_cpu = psutil.cpu_percent(interval=0.1)
            print(f'  {elapsed}/{duration} segundos... CPU: {current_cpu:.1f}% | RAM: {current_mem.percent:.1f}%')
except KeyboardInterrupt:
    print('\\n  Interrumpido por usuario')
finally:
    # Limpiar
    cpu_pool.terminate()
    cpu_pool.join()
    for p in ram_procs:
        p.terminate()
        p.join()

print('')
print('Carga completada')
"
}

simulate_both() {
    local duration=$1
    local target_ip=$2
    local target_port=$3
    
    echo -e "${BLUE}[INFO]${NC} Simulando tráfico de red Y carga de CPU simultáneamente..."
    echo -e "  Duración: ${duration} segundos"
    echo ""
    
    # Ejecutar ambos en background
    simulate_network "$duration" "$target_ip" "$target_port" &
    NETWORK_PID=$!
    
    simulate_cpu "$duration" &
    CPU_PID=$!
    
    # Esperar a que ambos terminen
    wait $NETWORK_PID
    wait $CPU_PID
}

# Parsear argumentos
MODE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --network|-n)
            MODE="network"
            shift
            ;;
        --cpu|-c)
            MODE="cpu"
            shift
            ;;
        --both|-b)
            MODE="both"
            shift
            ;;
        --duration|-d)
            DURATION="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}[ERROR]${NC} Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Si no se especificó modo, mostrar ayuda
if [ -z "$MODE" ]; then
    show_help
    exit 0
fi

# Verificar que docker compose está disponible
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker no está instalado o no está en PATH"
    exit 1
fi

# Verificar que estamos en el directorio correcto o cambiar
if [ ! -f "docker-compose.yml" ]; then
    if [ -f "PF_backend/ProyectoFinal_Backend/docker-compose.yml" ]; then
        cd PF_backend/ProyectoFinal_Backend
    else
        echo -e "${RED}[ERROR]${NC} No se encontró docker-compose.yml"
        echo -e "${YELLOW}[INFO]${NC} Ejecuta este script desde el directorio del proyecto"
        exit 1
    fi
fi

# Verificar que el contenedor está corriendo
if ! docker compose ps ml-pipeline | grep -q "Up"; then
    echo -e "${RED}[ERROR]${NC} El contenedor ml-pipeline no está corriendo"
    echo -e "${YELLOW}[INFO]${NC} Ejecuta: docker compose up -d ml-pipeline"
    exit 1
fi

echo "=========================================="
echo "SIMULADOR DE ACTIVIDAD SOSPECHOSA"
echo "=========================================="
echo ""

# Ejecutar según el modo
case $MODE in
    network)
        simulate_network "$DURATION" "$TARGET_IP" "$TARGET_PORT"
        ;;
    cpu)
        simulate_cpu "$DURATION"
        ;;
    both)
        simulate_both "$DURATION" "$TARGET_IP" "$TARGET_PORT"
        ;;
esac

echo ""
echo -e "${GREEN}[SUCCESS]${NC} ✅ Simulación completada"
echo -e "${BLUE}[INFO]${NC} Revisa los logs: docker compose logs -f ml-pipeline"
echo -e "${BLUE}[INFO]${NC} El modelo ML debería detectar actividad sospechosa en ~10-20 segundos"

