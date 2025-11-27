import { useEffect, useState } from 'react';
import { Settings, Plus, ToggleLeft, ToggleRight, RefreshCw } from 'lucide-react';
import { apiService, Rule, CreateRuleDto } from '../services/api';
import { format } from 'date-fns';

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<CreateRuleDto>({
    vendor: 'suricata',
    sid: 0,
    name: '',
    body: '',
    tags: [],
    enabled: true,
  });

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      setLoading(true);
      const data = await apiService.getRules();
      console.log('Rules loaded:', data); // Debug: ver qué se recibe
      setRules(data);
    } catch (error) {
      console.error('Error loading rules:', error);
      alert('Error al cargar las reglas. Revisa la consola para más detalles.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiService.createRule(formData);
      setShowCreateForm(false);
      setFormData({
        vendor: 'suricata',
        sid: 0,
        name: '',
        body: '',
        tags: [],
        enabled: true,
      });
      loadRules();
    } catch (error) {
      console.error('Error creating rule:', error);
      alert('Error al crear la regla');
    }
  };

  const handleToggleRule = async (id: string, enabled: boolean) => {
    try {
      await apiService.toggleRule(id, !enabled);
      loadRules();
    } catch (error) {
      console.error('Error toggling rule:', error);
    }
  };

  const handleTagInput = (value: string) => {
    const tags = value.split(',').map((t) => t.trim()).filter(Boolean);
    setFormData((prev) => ({ ...prev, tags }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Reglas de Detección</h1>
          <p className="text-slate-400">Gestiona las reglas de detección de cryptojacking</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={loadRules}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Actualizar
          </button>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nueva Regla
          </button>
        </div>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Crear Nueva Regla</h2>
          <form onSubmit={handleCreateRule} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Vendor
                </label>
                <select
                  value={formData.vendor}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      vendor: e.target.value as 'suricata' | 'snort',
                    }))
                  }
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="suricata">Suricata</option>
                  <option value="snort">Snort</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  SID
                </label>
                <input
                  type="number"
                  value={formData.sid}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, sid: parseInt(e.target.value) }))
                  }
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Nombre
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, name: e.target.value }))
                }
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Cuerpo de la Regla
              </label>
              <textarea
                value={formData.body}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, body: e.target.value }))
                }
                rows={4}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Tags (separados por comas)
              </label>
              <input
                type="text"
                onChange={(e) => handleTagInput(e.target.value)}
                placeholder="cryptojacking, mining, xmr"
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="enabled"
                checked={formData.enabled}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, enabled: e.target.checked }))
                }
                className="w-4 h-4 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500"
              />
              <label htmlFor="enabled" className="text-sm text-slate-300">
                Habilitada
              </label>
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Crear Regla
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Rules List */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : rules.length === 0 ? (
          <div className="text-center py-12">
            <Settings className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400 text-lg">No hay reglas configuradas</p>
          </div>
        ) : (
          <div className="space-y-4">
            {rules.map((rule) => (
              <div
                key={rule.id}
                className="bg-slate-700 rounded-lg p-6 border border-slate-600"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white">
                        {rule.name || rule.pattern}
                      </h3>
                      <span
                        className={`px-2 py-1 rounded text-xs font-semibold ${
                          rule.enabled
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-slate-600 text-slate-400'
                        }`}
                      >
                        {rule.enabled ? 'Activa' : 'Inactiva'}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {rule.vendor && (
                        <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                          {rule.vendor}
                        </span>
                      )}
                      {rule.sid && (
                        <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded text-xs">
                          SID: {rule.sid}
                        </span>
                      )}
                      {rule.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-slate-600 text-slate-300 rounded text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    {rule.body && (
                      <pre className="bg-slate-900 rounded p-3 text-xs text-slate-300 overflow-x-auto mb-2">
                        {rule.body}
                      </pre>
                    )}
                    <p className="text-xs text-slate-500">
                      Creada: {format(new Date(rule.createdAt), "PPpp")}
                    </p>
                  </div>
                  <button
                    onClick={() => handleToggleRule(rule.id, rule.enabled)}
                    className="ml-4 p-2 hover:bg-slate-600 rounded-lg transition-colors"
                    title={rule.enabled ? 'Deshabilitar' : 'Habilitar'}
                  >
                    {rule.enabled ? (
                      <ToggleRight className="w-6 h-6 text-green-400" />
                    ) : (
                      <ToggleLeft className="w-6 h-6 text-slate-400" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

