import { useState } from 'react';
import { Upload, CheckCircle, XCircle, Loader } from 'lucide-react';
import { apiService, IngestEveDto } from '../services/api';

export default function IngestPage() {
  const [formData, setFormData] = useState<IngestEveDto>({
    host_id: '',
    events: [],
  });
  const [eventJson, setEventJson] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      // Parse events from JSON string
      let events: Array<Record<string, unknown>> = [];
      if (eventJson.trim()) {
        try {
          events = JSON.parse(eventJson);
          if (!Array.isArray(events)) {
            throw new Error('Los eventos deben ser un array');
          }
        } catch (parseError) {
          setResult({
            success: false,
            message: 'Error al parsear JSON: ' + (parseError as Error).message,
          });
          setLoading(false);
          return;
        }
      }

      const data: IngestEveDto = {
        host_id: formData.host_id,
        events,
      };

      const response = await apiService.ingestEve(data);
      setResult({
        success: true,
        message: `Eventos ingeridos exitosamente: ${response.n}. Revisa la pestaña de Alertas para ver las detecciones.`,
      });
      setFormData({ host_id: '', events: [] });
      setEventJson('');
    } catch (error: any) {
      setResult({
        success: false,
        message: error.response?.data?.message || error.message || 'Error desconocido',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadExample = () => {
    setFormData({ host_id: 'flarevm01', events: [] });
    setEventJson(
      JSON.stringify(
        [
          {
            event_type: 'tls',
            tls: {
              sni: 'pool.minexmr.com',
            },
          },
        ],
        null,
        2
      )
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Ingestión de Eventos</h1>
        <p className="text-slate-400">
          Envía eventos EVE (Eve JSON) al sistema para su procesamiento
        </p>
      </div>

      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Host ID
            </label>
            <input
              type="text"
              value={formData.host_id}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, host_id: e.target.value }))
              }
              placeholder="Ej: flarevm01, remnux01"
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-slate-300">
                Eventos (JSON Array)
              </label>
              <button
                type="button"
                onClick={loadExample}
                className="text-sm text-blue-400 hover:text-blue-300"
              >
                Cargar Ejemplo
              </button>
            </div>
            <textarea
              value={eventJson}
              onChange={(e) => setEventJson(e.target.value)}
              rows={12}
              placeholder='[{"event_type":"tls","tls":{"sni":"pool.minexmr.com"}}]'
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="text-xs text-slate-500 mt-2">
              Ingresa un array JSON de eventos EVE. Cada evento debe tener un campo{' '}
              <code className="text-blue-400">event_type</code>.
            </p>
          </div>

          {result && (
            <div
              className={`p-4 rounded-lg flex items-center gap-3 ${
                result.success
                  ? 'bg-green-500/10 border border-green-500/20'
                  : 'bg-red-500/10 border border-red-500/20'
              }`}
            >
              {result.success ? (
                <CheckCircle className="w-5 h-5 text-green-400" />
              ) : (
                <XCircle className="w-5 h-5 text-red-400" />
              )}
              <p
                className={
                  result.success ? 'text-green-400' : 'text-red-400'
                }
              >
                {result.message}
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
          >
            {loading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Procesando...
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                Ingerir Eventos
              </>
            )}
          </button>
        </form>
      </div>

      {/* Documentation */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Ejemplos de Eventos</h2>
        <div className="space-y-4">
          <div>
            <p className="text-sm text-slate-400 mb-2">Evento TLS (SNI):</p>
            <pre className="bg-slate-900 rounded p-3 text-xs text-slate-300 overflow-x-auto">
              {JSON.stringify(
                {
                  event_type: 'tls',
                  tls: {
                    sni: 'pool.minexmr.com',
                  },
                },
                null,
                2
              )}
            </pre>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-2">Evento DNS:</p>
            <pre className="bg-slate-900 rounded p-3 text-xs text-slate-300 overflow-x-auto">
              {JSON.stringify(
                {
                  event_type: 'dns',
                  dns: {
                    rrname: 'supportxmr.com',
                  },
                },
                null,
                2
              )}
            </pre>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-2">Múltiples Eventos:</p>
            <pre className="bg-slate-900 rounded p-3 text-xs text-slate-300 overflow-x-auto">
              {JSON.stringify(
                [
                  {
                    event_type: 'dns',
                    dns: { rrname: 'supportxmr.com' },
                  },
                  {
                    event_type: 'tls',
                    tls: { sni: 'github.com' },
                  },
                  {
                    event_type: 'tls',
                    tls: { sni: 'hashvault.pro' },
                  },
                ],
                null,
                2
              )}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

