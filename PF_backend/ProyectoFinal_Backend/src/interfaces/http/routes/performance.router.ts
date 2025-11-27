import { Router } from "express";
import * as si from "systeminformation";

const router = Router();

// Cache para almacenar métricas previas (para calcular diferencias)
let previousStats: {
  networkStats?: any;
  fsStats?: any;
  timestamp?: number;
} = {};

router.get("/metrics", async (_req, res) => {
  try {
    const timestamp = Date.now();
    
    // Obtener métricas en paralelo
    const [cpu, mem, networkStats, fsStats, fsSize] = await Promise.all([
      si.currentLoad(),
      si.mem(),
      si.networkStats(),
      si.fsStats(),
      si.fsSize(),
    ]);

    // Calcular CPU usage
    const cpuUsage = cpu.currentLoad || 0;

    // Calcular memoria usage
    const memTotal = mem.total;
    const memUsed = mem.used;
    const memUsage = memTotal > 0 ? (memUsed / memTotal) * 100 : 0;

    // Calcular tráfico de red (diferencia desde la última medición)
    let networkIn = 0;
    let networkOut = 0;
    
    if (previousStats.networkStats && previousStats.timestamp) {
      const timeDiff = (timestamp - previousStats.timestamp) / 1000; // segundos
      const statsArray = Array.isArray(networkStats) ? networkStats : [networkStats];
      const prevStatsArray = Array.isArray(previousStats.networkStats) 
        ? previousStats.networkStats 
        : [previousStats.networkStats];
      
      // Sumar todas las interfaces de red
      let totalBytesRecv = 0;
      let totalBytesSent = 0;
      let prevTotalBytesRecv = 0;
      let prevTotalBytesSent = 0;
      
      statsArray.forEach((stat: any) => {
        if (stat && typeof stat.bytes_recv === 'number') {
          totalBytesRecv += stat.bytes_recv;
        }
        if (stat && typeof stat.bytes_sent === 'number') {
          totalBytesSent += stat.bytes_sent;
        }
      });
      
      prevStatsArray.forEach((stat: any) => {
        if (stat && typeof stat.bytes_recv === 'number') {
          prevTotalBytesRecv += stat.bytes_recv;
        }
        if (stat && typeof stat.bytes_sent === 'number') {
          prevTotalBytesSent += stat.bytes_sent;
        }
      });
      
      if (timeDiff > 0) {
        networkIn = ((totalBytesRecv - prevTotalBytesRecv) / timeDiff) / 1024; // KB/s
        networkOut = ((totalBytesSent - prevTotalBytesSent) / timeDiff) / 1024; // KB/s
      }
    }

    // Calcular I/O de disco (diferencia desde la última medición)
    let diskRead = 0;
    let diskWrite = 0;
    
    if (previousStats.fsStats && previousStats.timestamp) {
      const timeDiff = (timestamp - previousStats.timestamp) / 1000; // segundos
      const statsArray = Array.isArray(fsStats) ? fsStats : [fsStats];
      const prevStatsArray = Array.isArray(previousStats.fsStats) 
        ? previousStats.fsStats 
        : [previousStats.fsStats];
      
      // Sumar todas las particiones
      let totalRx = 0;
      let totalWx = 0;
      let prevTotalRx = 0;
      let prevTotalWx = 0;
      
      statsArray.forEach((stat: any) => {
        if (stat && typeof stat.rx === 'number') {
          totalRx += stat.rx;
        }
        if (stat && typeof stat.wx === 'number') {
          totalWx += stat.wx;
        }
      });
      
      prevStatsArray.forEach((stat: any) => {
        if (stat && typeof stat.rx === 'number') {
          prevTotalRx += stat.rx;
        }
        if (stat && typeof stat.wx === 'number') {
          prevTotalWx += stat.wx;
        }
      });
      
      if (timeDiff > 0) {
        diskRead = ((totalRx - prevTotalRx) / timeDiff) / (1024 * 1024); // MB/s
        diskWrite = ((totalWx - prevTotalWx) / timeDiff) / (1024 * 1024); // MB/s
      }
    }

    // Calcular uso de disco (porcentaje de espacio ocupado)
    let diskUsage = 0;
    if (fsSize && Array.isArray(fsSize) && fsSize.length > 0) {
      // Usar la partición principal (generalmente la primera o la del sistema)
      const mainPartition = fsSize.find((p: any) => p.mount === '/' || p.mount === 'C:\\' || p.mount === '/') || fsSize[0];
      if (mainPartition && mainPartition.size && mainPartition.used) {
        diskUsage = (mainPartition.used / mainPartition.size) * 100;
      }
    }

    // Guardar stats actuales para la próxima medición
    previousStats = {
      networkStats,
      fsStats,
      timestamp,
    };

    res.json({
      cpu: Math.round(cpuUsage * 100) / 100,
      memory: Math.round(memUsage * 100) / 100,
      networkIn: Math.max(0, Math.round(networkIn * 100) / 100),
      networkOut: Math.max(0, Math.round(networkOut * 100) / 100),
      diskUsage: Math.round(diskUsage * 100) / 100, // Porcentaje de espacio ocupado
      diskRead: Math.max(0, Math.round(diskRead * 100) / 100), // Velocidad de lectura
      diskWrite: Math.max(0, Math.round(diskWrite * 100) / 100), // Velocidad de escritura
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Error obteniendo métricas:", error);
    res.status(500).json({ error: "Error al obtener métricas del sistema" });
  }
});

export default router;

