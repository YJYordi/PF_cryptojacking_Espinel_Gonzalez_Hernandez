import { useEffect, useState } from 'react';
import { AlertTriangle, Shield, Activity, TrendingUp, RefreshCw } from 'lucide-react';
import { apiService, Alert } from '../services/api';
import { format } from 'date-fns';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalAlerts: 0,
    totalRules: 0,
    enabledRules: 0,
    recentAlerts: 0,
  });
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
    
    // Actualizar cuando la página vuelve a estar visible
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadData();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Debug: mostrar stats cuando cambien
  useEffect(() => {
    console.log('Dashboard: Stats updated', stats);
  }, [stats]);

  const loadData = async (showRefreshing = false) => {
    try {
      if (showRefreshing) {
        setRefreshing(true);
      }
      
      // Cargar reglas siempre (esto es lo más importante)
      const rules = await apiService.getRules();
      console.log('Dashboard: Rules loaded', rules);
      const enabledRules = rules.filter((r) => r.enabled === true).length;
      const totalRules = rules.length;
      
      console.log('Dashboard: Stats calculated', {
        totalRules,
        enabledRules,
        rules: rules.map(r => ({ pattern: r.pattern, enabled: r.enabled }))
      });
      
      // Intentar cargar alertas, pero no fallar si hay error
      let alerts: Alert[] = [];
      let totalAlerts = 0;
      let recentAlertsCount = 0;
      
      try {
        alerts = await apiService.getAlerts();
        totalAlerts = alerts.length;
        recentAlertsCount = alerts.filter(
          (a) => new Date(a.createdAt) > new Date(Date.now() - 24 * 60 * 60 * 1000)
        ).length;
      } catch (alertError) {
        console.warn('Error loading alerts (non-critical):', alertError);
        // Continuar sin alertas
      }

      const newStats = {
        totalAlerts,
        totalRules,
        enabledRules,
        recentAlerts: recentAlertsCount,
      };
      
      console.log('Dashboard: Setting stats', newStats);
      setStats(newStats);

      setRecentAlerts(alerts.slice(0, 5));
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    loadData(true);
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
          <p className="text-slate-400">Vista general del sistema IDS Cryptojacking</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Alertas"
          value={stats.totalAlerts}
          icon={AlertTriangle}
          color="red"
        />
        <StatCard
          title="Reglas Activas"
          value={stats.enabledRules ?? 0}
          subtitle={`de ${stats.totalRules ?? 0} totales`}
          icon={Shield}
          color="blue"
        />
        <StatCard
          title="Alertas (24h)"
          value={stats.recentAlerts}
          icon={TrendingUp}
          color="yellow"
        />
        <StatCard
          title="Estado"
          value="Operativo"
          icon={Activity}
          color="green"
        />
      </div>

      {/* Recent Alerts */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Alertas Recientes</h2>
        {recentAlerts.length === 0 ? (
          <p className="text-slate-400">No hay alertas recientes</p>
        ) : (
          <div className="space-y-3">
            {recentAlerts.map((alert) => (
              <div
                key={alert.id}
                className="bg-slate-700 rounded-lg p-4 border border-slate-600"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className={`px-2 py-1 rounded text-xs font-semibold ${
                          alert.severity === 'high'
                            ? 'bg-red-500/20 text-red-400'
                            : alert.severity === 'medium'
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : 'bg-blue-500/20 text-blue-400'
                        }`}
                      >
                        {alert.severity.toUpperCase()}
                      </span>
                      <span className="text-sm text-slate-400">
                        Host: {alert.event?.hostId || 'N/A'}
                      </span>
                    </div>
                    <p className="text-sm text-slate-300">
                      Tipo: {alert.event?.kind || 'unknown'}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      {format(new Date(alert.createdAt), "PPpp")}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'red' | 'blue' | 'yellow' | 'green';
}) {
  const colorClasses = {
    red: 'bg-red-500/10 border-red-500/20 text-red-400',
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
    yellow: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
    green: 'bg-green-500/10 border-green-500/20 text-green-400',
  };

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-slate-400">{title}</h3>
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div>
        <p className="text-3xl font-bold text-white">{value}</p>
        {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
}

