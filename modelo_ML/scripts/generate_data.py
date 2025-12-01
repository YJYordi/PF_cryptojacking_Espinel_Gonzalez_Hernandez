import psutil  # type: ignore
import pandas as pd  # type: ignore
import time
import sys
import csv
from datetime import datetime

# -----------------------------------------
# 1. LEER EL MODO DESDE EL ARGUMENTO
# -----------------------------------------
if len(sys.argv) < 2:
    print("Uso: python recolector.py <normal|carga|minado>")
    sys.exit(1)

modo = sys.argv[1].lower()

if modo not in ["normal", "carga", "minado"]:
    print("Modo inválido. Usa: normal, carga o minado")
    sys.exit(1)

label = 1 if modo == "minado" else 0
print(f"[INFO] Recolector iniciado en modo '{modo}' (label={label})")


# -----------------------------------------
# 2. ARCHIVO CSV / APPEND
# -----------------------------------------
import os
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DATASET_FILE = os.path.join(DATA_DIR, "dataset.csv")

# Si el archivo NO existe, creamos encabezado
try:
    open(DATASET_FILE, "x").close()
    header_needed = True
except FileExistsError:
    header_needed = False


# -----------------------------------------
# 3. CONFIGURACIÓN DE COLUMNA
# -----------------------------------------
COLUMNAS = [
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


# -----------------------------------------
# 4. BUCLE DE RECOLECCIÓN
# -----------------------------------------
print("[INFO] Recolectando datos... CTRL + C para detener")

with open(DATASET_FILE, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    if header_needed:
        writer.writerow(COLUMNAS)

    prev_net = psutil.net_io_counters()
    time.sleep(1)

    while True:
        try:
            timestamp = datetime.now().isoformat()
            cpu_percent = psutil.cpu_percent()
            ram_percent = psutil.virtual_memory().percent

            net = psutil.net_io_counters()
            bytes_sent = net.bytes_sent - prev_net.bytes_sent
            bytes_recv = net.bytes_recv - prev_net.bytes_recv
            prev_net = net

            # Procesos activos
            procesos = []
            xmrig_detected = False

            for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
                try:
                    name = p.info["name"] or "unknown"
                    cpu_p = p.info["cpu_percent"]
                    mem_p = p.info["memory_percent"]

                    procesos.append(f"{name}:{cpu_p:.1f}:{mem_p:.1f}")

                    if "xmrig" in name.lower():
                        xmrig_detected = True

                except psutil.NoSuchProcess:
                    continue

            process_list_str = "|".join(procesos)
            process_count = len(procesos)

            fila = [
                timestamp,
                cpu_percent,
                ram_percent,
                bytes_sent,
                bytes_recv,
                process_count,
                process_list_str,
                int(xmrig_detected),
                label
            ]

            writer.writerow(fila)
            f.flush()

            print(f"[OK] {timestamp}  CPU={cpu_percent}%  RAM={ram_percent}%  XMrig={xmrig_detected}")

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n[INFO] Recolector detenido por el usuario.")
            break
