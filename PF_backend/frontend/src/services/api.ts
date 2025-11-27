import axios from 'axios';
import type { Rule, CreateRuleDto, Alert, IngestEveDto } from './types';

// El frontend y backend están en el mismo servidor, usar rutas relativas
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Re-exportar tipos para compatibilidad
export type { Rule, CreateRuleDto, Alert, IngestEveDto };

export const apiService = {
  // Health check
  healthCheck: async () => {
    const response = await api.get('/healthz');
    return response.data;
  },

  // Rules
  getRules: async (): Promise<Rule[]> => {
    const response = await api.get('/rulesets/');
    return response.data;
  },

  createRule: async (rule: CreateRuleDto): Promise<Rule> => {
    const response = await api.post('/rulesets/rules', rule);
    return response.data;
  },

  toggleRule: async (id: string, _enabled: boolean): Promise<void> => {
    await api.patch(`/rulesets/${id}/toggle`);
  },

  // Alerts
  getAlerts: async (params?: { host_id?: string; since?: string }): Promise<Alert[]> => {
    const response = await api.get('/alerts/', { params });
    return response.data;
  },

  // Ingest
  ingestEve: async (data: IngestEveDto): Promise<{ ok: boolean; n: number }> => {
    const response = await api.post('/ingest/eve', data);
    return response.data;
  },

  // Performance
  getPerformanceMetrics: async (): Promise<{
    cpu: number;
    memory: number;
    networkIn: number;
    networkOut: number;
    diskUsage: number;
    diskRead: number;
    diskWrite: number;
    timestamp: string;
  }> => {
    const response = await api.get('/performance/metrics');
    return response.data;
  },
};

export default api;
