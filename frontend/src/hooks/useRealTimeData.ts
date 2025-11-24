/**
 * Custom hooks for real-time data with auto-refresh
 */

import { useQuery } from '@tanstack/react-query';
import { REFRESH_INTERVALS } from '@/constants/config';
import * as api from '@/services/api';
import type { DateRangeParams, ZoneFilterParams } from '@/types/api';

// Real-time LBMP (5-minute refresh)
export const useRealTimeLBMP = (params?: ZoneFilterParams) => {
  return useQuery({
    queryKey: ['realtime-lbmp', params],
    queryFn: () => api.fetchRealTimeLBMP(params),
    refetchInterval: REFRESH_INTERVALS.REAL_TIME,
  });
};

// Real-time Load (5-minute refresh)
export const useRealTimeLoad = (params?: ZoneFilterParams) => {
  return useQuery({
    queryKey: ['realtime-load', params],
    queryFn: () => api.fetchRealTimeLoad(params),
    refetchInterval: REFRESH_INTERVALS.REAL_TIME,
  });
};

// Constraints (5-minute refresh)
export const useConstraints = (params?: DateRangeParams & { market_type?: 'realtime' | 'dayahead' }) => {
  return useQuery({
    queryKey: ['constraints', params],
    queryFn: () => api.fetchConstraints(params),
    refetchInterval: REFRESH_INTERVALS.REAL_TIME,
  });
};

// Interface Flows (5-minute refresh)
export const useInterfaceFlows = (params?: DateRangeParams) => {
  return useQuery({
    queryKey: ['interface-flows', params],
    queryFn: () => api.fetchInterfaceFlows(params),
    refetchInterval: REFRESH_INTERVALS.REAL_TIME,
  });
};

// Interregional Flows (5-minute refresh)
export const useInterregionalFlows = (params?: DateRangeParams) => {
  return useQuery({
    queryKey: ['interregional-flows', params],
    queryFn: () => api.fetchInterregionalFlows(params),
    refetchInterval: REFRESH_INTERVALS.REAL_TIME,
  });
};

// Market Advisories (5-minute refresh)
export const useMarketAdvisories = (params?: DateRangeParams) => {
  return useQuery({
    queryKey: ['market-advisories', params],
    queryFn: () => api.fetchMarketAdvisories(params),
    refetchInterval: REFRESH_INTERVALS.REAL_TIME,
  });
};

// Trading Signals (5-minute refresh)
export const useTradingSignals = (params?: { limit?: number }) => {
  return useQuery({
    queryKey: ['trading-signals', params],
    queryFn: () => api.fetchTradingSignals(params as any),
    refetchInterval: REFRESH_INTERVALS.REAL_TIME,
  });
};

