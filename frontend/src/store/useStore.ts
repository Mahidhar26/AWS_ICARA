import { create } from 'zustand';

export interface Alert {
  id: string;
  type: 'COMMUNICATION' | 'TRANSACTION';
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;
  title: string;
  description: string;
  timestamp: string;
  status: 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'FALSE_POSITIVE';
  violations?: Array<{
    type: string;
    regulation: string;
    explanation: string;
  }>;
}

export interface Metrics {
  totalAlerts: number;
  falsePositiveRate: number;
  costSavings: number;
  processingVolume: number;
  averageProcessingTime: number;
  criticalAlerts: number;
  highAlerts: number;
  mediumAlerts: number;
  lowAlerts: number;
}

interface AppState {
  alerts: Alert[];
  metrics: Metrics;
  isLoading: boolean;
  error: string | null;
  filters: {
    riskLevel: string[];
    type: string[];
    status: string[];
    dateRange: [Date | null, Date | null];
  };
  setAlerts: (alerts: Alert[]) => void;
  setMetrics: (metrics: Metrics) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  updateFilters: (filters: Partial<AppState['filters']>) => void;
  addAlert: (alert: Alert) => void;
  updateAlertStatus: (alertId: string, status: Alert['status']) => void;
}

export const useStore = create<AppState>((set, get) => ({
  alerts: [],
  metrics: {
    totalAlerts: 0,
    falsePositiveRate: 0,
    costSavings: 0,
    processingVolume: 0,
    averageProcessingTime: 0,
    criticalAlerts: 0,
    highAlerts: 0,
    mediumAlerts: 0,
    lowAlerts: 0,
  },
  isLoading: false,
  error: null,
  filters: {
    riskLevel: [],
    type: [],
    status: [],
    dateRange: [null, null],
  },
  setAlerts: (alerts) => set({ alerts }),
  setMetrics: (metrics) => set({ metrics }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  updateFilters: (newFilters) => 
    set((state) => ({ 
      filters: { ...state.filters, ...newFilters } 
    })),
  addAlert: (alert) => 
    set((state) => ({ 
      alerts: [alert, ...state.alerts] 
    })),
  updateAlertStatus: (alertId, status) =>
    set((state) => ({
      alerts: state.alerts.map(alert =>
        alert.id === alertId ? { ...alert, status } : alert
      ),
    })),
}));