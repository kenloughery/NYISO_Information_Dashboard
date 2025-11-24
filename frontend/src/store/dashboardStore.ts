/**
 * Zustand store for dashboard state management
 */

import { create } from 'zustand';

interface DashboardState {
  // User preferences
  selectedZones: string[];
  selectedTimeRange: '1h' | '6h' | '24h' | '7d' | '30d';
  
  // UI state
  sidebarOpen: boolean;
  activeSection: string | null;
  
  // Portfolio (for future P&L tracking)
  portfolioPositions: Array<{
    id: string;
    zone: string;
    type: 'spread' | 'energy';
    entryPrice: number;
    quantity: number;
  }>;
  
  // Alert filters
  alertFilters: {
    severity: ('info' | 'warning' | 'critical')[];
    signalTypes: string[];
  };
  
  // Actions
  setSelectedZones: (zones: string[]) => void;
  setSelectedTimeRange: (range: DashboardState['selectedTimeRange']) => void;
  toggleSidebar: () => void;
  setActiveSection: (section: string | null) => void;
  addPortfolioPosition: (position: DashboardState['portfolioPositions'][0]) => void;
  removePortfolioPosition: (id: string) => void;
  updateAlertFilters: (filters: Partial<DashboardState['alertFilters']>) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  // Initial state
  selectedZones: [],
  selectedTimeRange: '24h',
  sidebarOpen: true,
  activeSection: null,
  portfolioPositions: [],
  alertFilters: {
    severity: ['info', 'warning', 'critical'],
    signalTypes: [],
  },
  
  // Actions
  setSelectedZones: (zones) => set({ selectedZones: zones }),
  setSelectedTimeRange: (range) => set({ selectedTimeRange: range }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setActiveSection: (section) => set({ activeSection: section }),
  addPortfolioPosition: (position) =>
    set((state) => ({
      portfolioPositions: [...state.portfolioPositions, position],
    })),
  removePortfolioPosition: (id) =>
    set((state) => ({
      portfolioPositions: state.portfolioPositions.filter((p) => p.id !== id),
    })),
  updateAlertFilters: (filters) =>
    set((state) => ({
      alertFilters: { ...state.alertFilters, ...filters },
    })),
}));

