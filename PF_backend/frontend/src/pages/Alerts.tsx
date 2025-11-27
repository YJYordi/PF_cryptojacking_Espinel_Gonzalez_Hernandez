import { useEffect, useState } from 'react';
import { AlertTriangle, Filter, RefreshCw } from 'lucide-react';
import { apiService, Alert } from '../services/api';
import { format } from 'date-fns';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    host_id: '',
    since: '',
  });

  useEffect(() => {
    loadAlerts();
  }, [filters]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const params: { host_id?: string; since?: string } = {};
      if (filters.host_id) params.host_id = filters.host_id;
      if (filters.since) params.since = filters.since;

      const data = await apiService.getAlerts(params);
      setAlerts(data);
    } catch (error) {
      console.error('Error loading alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({ host_id: '', since: '' });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Alertas</h1>
          <p className="text-slate-400">Gestión y visualización de alertas de seguridad</p>
        </div>
        <button
          onClick={loadAlerts}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Actualizar
        </button>
      </div>

      {/* Filters */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-slate-400" />
          <h2 className="text-lg font-semibold text-white">Filtros</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Host ID
            </label>
            <input
              type="text"
              value={filters.host_id}
              onChange={(e) => handleFilterChange('host_id', e.target.value)}
              placeholder="Ej: flarevm01"
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Desde (fecha)
            </label>
            <input
              type="datetime-local"
              value={filters.since}
              onChange={(e) => handleFilterChange('since', e.target.value)}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={clearFilters}
              className="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
            >
              Limpiar Filtros
            </button>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-12">
            <AlertTriangle className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400 text-lg">No se encontraron alertas</p>
          </div>
        ) : (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="bg-slate-700 rounded-lg p-6 border border-slate-600 hover:border-slate-500 transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2 rounded-lg ${
                        alert.severity === 'high'
                          ? 'bg-red-500/20 text-red-400'
                          : alert.severity === 'medium'
                          ? 'bg-yellow-500/20 text-yellow-400'
                          : 'bg-blue-500/20 text-blue-400'
                      }`}
                    >
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">
                        Alerta {alert.id.slice(0, 8)}
                      </h3>
                      <p className="text-sm text-slate-400">
                        {format(new Date(alert.createdAt), "PPpp")}
                      </p>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      alert.severity === 'high'
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                        : alert.severity === 'medium'
                        ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                        : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    }`}
                  >
                    {alert.severity.toUpperCase()}
                  </span>
                </div>

                {/* Información de Suricata */}
                {alert.reason?.suricata_sid && (
                  <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-semibold text-blue-400">SURICATA DETECTION</span>
                      <span className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs font-mono">
                        SID: {alert.reason.suricata_sid}
                      </span>
                    </div>
                    <p className="text-sm text-blue-300 font-semibold mb-1">
                      {alert.reason.suricata_msg}
                    </p>
                    <p className="text-xs text-blue-400">
                      Regla: {alert.reason.rule_name}
                    </p>
                  </div>
                )}

                {/* Información de red */}
                {alert.event?.payload?.src_ip && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-slate-400 mb-1">Origen</p>
                      <p className="text-white font-mono text-sm">
                        {alert.event.payload.src_ip}:{alert.event.payload.src_port}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">Destino</p>
                      <p className="text-white font-mono text-sm">
                        {alert.event.payload.dest_ip}:{alert.event.payload.dest_port}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">Protocolo</p>
                      <p className="text-white font-mono text-sm">{alert.event.payload.proto}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">Host ID</p>
                      <p className="text-white font-mono text-sm">{alert.event?.hostId || 'N/A'}</p>
                    </div>
                  </div>
                )}

                {/* Información TLS/DNS */}
                {alert.event?.payload?.tls && (
                  <div className="mb-4 p-3 bg-slate-900 rounded">
                    <p className="text-sm text-slate-400 mb-2">Información TLS</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-slate-500">SNI:</span>{' '}
                        <span className="text-yellow-400 font-mono">{alert.event.payload.tls.sni}</span>
                      </div>
                      {alert.event.payload.tls.version && (
                        <div>
                          <span className="text-slate-500">Versión:</span>{' '}
                          <span className="text-slate-300">{alert.event.payload.tls.version}</span>
                        </div>
                      )}
                      {alert.event.payload.tls.cipher && (
                        <div className="md:col-span-2">
                          <span className="text-slate-500">Cipher:</span>{' '}
                          <span className="text-slate-300 text-xs">{alert.event.payload.tls.cipher}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {alert.event?.payload?.dns && (
                  <div className="mb-4 p-3 bg-slate-900 rounded">
                    <p className="text-sm text-slate-400 mb-2">Información DNS</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-slate-500">Dominio:</span>{' '}
                        <span className="text-yellow-400 font-mono">{alert.event.payload.dns.rrname}</span>
                      </div>
                      {alert.event.payload.dns.rrtype && (
                        <div>
                          <span className="text-slate-500">Tipo:</span>{' '}
                          <span className="text-slate-300">{alert.event.payload.dns.rrtype}</span>
                        </div>
                      )}
                      {alert.event.payload.dns.rdata && (
                        <div>
                          <span className="text-slate-500">IP Resuelta:</span>{' '}
                          <span className="text-slate-300 font-mono">{alert.event.payload.dns.rdata}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Detalles de la alerta de Suricata */}
                {alert.event?.payload?.alert && (
                  <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <p className="text-sm text-red-400 mb-2 font-semibold">Detalles de Suricata</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-red-400">Signature ID:</span>{' '}
                        <span className="text-white font-mono">{alert.event.payload.alert.signature_id}</span>
                      </div>
                      <div>
                        <span className="text-red-400">Severity:</span>{' '}
                        <span className="text-white">{alert.event.payload.alert.severity}</span>
                      </div>
                      <div className="md:col-span-2">
                        <span className="text-red-400">Categoría:</span>{' '}
                        <span className="text-white">{alert.event.payload.alert.category}</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="mt-4">
                  <p className="text-sm text-slate-400 mb-2">Información de Detección</p>
                  <div className="bg-slate-900 rounded p-3 text-xs">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
                      <div>
                        <span className="text-slate-500">Confianza:</span>{' '}
                        <span className="text-yellow-400">
                          {(alert.reason?.confidence * 100 || 0).toFixed(0)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500">Tipo:</span>{' '}
                        <span className="text-slate-300">{alert.reason?.type || 'unknown'}</span>
                      </div>
                    </div>
                    {alert.reason?.indicators && (
                      <div>
                        <span className="text-slate-500">Indicadores:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {alert.reason.indicators.map((ind: string, idx: number) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-red-500/20 text-red-300 rounded text-xs"
                            >
                              {ind}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {alert.event?.payload && (
                  <div className="mt-4">
                    <p className="text-sm text-slate-400 mb-2">Payload del Evento</p>
                    <pre className="bg-slate-900 rounded p-3 text-xs text-slate-300 overflow-x-auto">
                      {JSON.stringify(alert.event.payload, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

