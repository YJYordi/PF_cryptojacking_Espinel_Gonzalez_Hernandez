import { useEffect, useState } from 'react';
import { Cpu, HardDrive, Network, TrendingUp } from 'lucide-react';
import { apiService } from '../services/api';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface PerformanceData {
  timestamp: string;
  cpu: number;
  memory: number;
  networkIn: number;
  networkOut: number;
  diskUsage: number;
  diskRead: number;
  diskWrite: number;
}

export default function PerformancePage() {
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
  const [currentStats, setCurrentStats] = useState({
    cpu: 0,
    memory: 0,
    networkIn: 0,
    networkOut: 0,
    diskUsage: 0,
    diskRead: 0,
    diskWrite: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
    const interval = setInterval(() => {
      fetchMetrics();
    }, 2000); // Actualizar cada 2 segundos

    return () => clearInterval(interval);
  }, []);

  const loadInitialData = async () => {
    try {
      // Cargar datos iniciales
      const initialData: PerformanceData[] = [];
      const now = Date.now();
      
      // Crear 30 puntos vacíos iniciales
      for (let i = 29; i >= 0; i--) {
        const timestamp = new Date(now - i * 2000);
        initialData.push({
          timestamp: timestamp.toLocaleTimeString(),
          cpu: 0,
          memory: 0,
          networkIn: 0,
          networkOut: 0,
          diskUsage: 0,
          diskRead: 0,
          diskWrite: 0,
        });
      }
      
      setPerformanceData(initialData);
      
      // Cargar primera métrica
      await fetchMetrics();
      setLoading(false);
    } catch (error) {
      console.error('Error cargando datos iniciales:', error);
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    try {
      const metrics = await apiService.getPerformanceMetrics();
      
      const newPoint: PerformanceData = {
        timestamp: new Date().toLocaleTimeString(),
        cpu: metrics.cpu,
        memory: metrics.memory,
        networkIn: metrics.networkIn,
        networkOut: metrics.networkOut,
        diskUsage: metrics.diskUsage || 0,
        diskRead: metrics.diskRead,
        diskWrite: metrics.diskWrite,
      };

      setPerformanceData((prev) => {
        const newData = [...prev];
        if (newData.length >= 30) {
          newData.shift(); // Mantener solo los últimos 30 puntos
        }
        newData.push(newPoint);
        return newData;
      });

      setCurrentStats(newPoint);
    } catch (error) {
      console.error('Error obteniendo métricas:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Rendimiento del Sistema</h1>
        <p className="text-slate-400">Monitoreo en tiempo real de recursos del sistema</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          title="CPU"
          value={`${currentStats.cpu.toFixed(1)}%`}
          icon={Cpu}
          color="blue"
          trend={currentStats.cpu > 80 ? 'high' : currentStats.cpu > 50 ? 'medium' : 'low'}
        />
        <StatCard
          title="Memoria"
          value={`${currentStats.memory.toFixed(1)}%`}
          icon={HardDrive}
          color="purple"
          trend={currentStats.memory > 80 ? 'high' : currentStats.memory > 50 ? 'medium' : 'low'}
        />
        <StatCard
          title="Red (Entrada)"
          value={`${(currentStats.networkIn / 1024).toFixed(2)} MB/s`}
          icon={Network}
          color="green"
          trend="low"
        />
        <StatCard
          title="Red (Salida)"
          value={`${(currentStats.networkOut / 1024).toFixed(2)} MB/s`}
          icon={Network}
          color="yellow"
          trend="low"
        />
        <StatCard
          title="Disco (Uso)"
          value={`${currentStats.diskUsage.toFixed(1)}%`}
          icon={HardDrive}
          color="cyan"
          trend={currentStats.diskUsage > 80 ? 'high' : currentStats.diskUsage > 50 ? 'medium' : 'low'}
        />
        <StatCard
          title="Disco (Lectura)"
          value={`${currentStats.diskRead.toFixed(0)} MB/s`}
          icon={HardDrive}
          color="cyan"
          trend="low"
        />
        <StatCard
          title="Disco (Escritura)"
          value={`${currentStats.diskWrite.toFixed(0)} MB/s`}
          icon={HardDrive}
          color="orange"
          trend="low"
        />
      </div>

      {/* CPU Usage Chart */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="w-5 h-5 text-blue-400" />
          <h2 className="text-xl font-semibold text-white">Uso de CPU</h2>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={performanceData}>
            <defs>
              <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="timestamp" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" domain={[0, 100]} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Area
              type="monotone"
              dataKey="cpu"
              stroke="#3b82f6"
              fillOpacity={1}
              fill="url(#colorCpu)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Memory Usage Chart */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <HardDrive className="w-5 h-5 text-purple-400" />
          <h2 className="text-xl font-semibold text-white">Uso de Memoria</h2>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={performanceData}>
            <defs>
              <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a855f7" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="timestamp" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" domain={[0, 100]} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Area
              type="monotone"
              dataKey="memory"
              stroke="#a855f7"
              fillOpacity={1}
              fill="url(#colorMemory)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Network Traffic Chart */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Network className="w-5 h-5 text-green-400" />
          <h2 className="text-xl font-semibold text-white">Tráfico de Red</h2>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={performanceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="timestamp" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="networkIn"
              stroke="#10b981"
              strokeWidth={2}
              name="Entrada (KB/s)"
            />
            <Line
              type="monotone"
              dataKey="networkOut"
              stroke="#eab308"
              strokeWidth={2}
              name="Salida (KB/s)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Disk I/O Chart */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <HardDrive className="w-5 h-5 text-cyan-400" />
          <h2 className="text-xl font-semibold text-white">I/O de Disco</h2>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={performanceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="timestamp" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Legend />
            <Bar dataKey="diskRead" fill="#06b6d4" name="Lectura (MB/s)" />
            <Bar dataKey="diskWrite" fill="#f97316" name="Escritura (MB/s)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
  trend,
}: {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  trend: 'high' | 'medium' | 'low';
}) {
  const colorClasses = {
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
    green: 'bg-green-500/10 border-green-500/20 text-green-400',
    yellow: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
    cyan: 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400',
    orange: 'bg-orange-500/10 border-orange-500/20 text-orange-400',
  };

  const trendColors = {
    high: 'text-red-400',
    medium: 'text-yellow-400',
    low: 'text-green-400',
  };

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-slate-400">{title}</h3>
        <div className={`p-2 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div>
        <p className={`text-3xl font-bold ${trendColors[trend]}`}>{value}</p>
        <div className="flex items-center gap-1 mt-2">
          <TrendingUp className={`w-4 h-4 ${trendColors[trend]}`} />
          <span className={`text-xs ${trendColors[trend]}`}>
            {trend === 'high' ? 'Alto' : trend === 'medium' ? 'Medio' : 'Normal'}
          </span>
        </div>
      </div>
    </div>
  );
}

