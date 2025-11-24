/**
 * NYISO API Client Service
 * Provides typed methods for all API endpoints
 */

import axios from 'axios';
import { API_BASE_URL } from '@/constants/config';
import type {
  Zone,
  Interface,
  RealTimeLBMP,
  DayAheadLBMP,
  TimeWeightedLBMP,
  RealTimeLoad,
  LoadForecast,
  InterfaceFlow,
  InterregionalFlow,
  MarketAdvisory,
  Constraint,
  AncillaryService,
  ExternalRTOPrice,
  ATCTTC,
  Outage,
  WeatherForecast,
  FuelMix,
  RTDASpread,
  ZoneSpread,
  LoadForecastError,
  ReserveMargin,
  PriceVolatility,
  Correlation,
  TradingSignal,
  Stats,
  DateRangeParams,
  ZoneFilterParams,
  WeatherForecastParams,
  ConstraintParams,
  AncillaryServiceParams,
  RTDASpreadParams,
  LoadForecastErrorParams,
  PriceVolatilityParams,
  CorrelationParams,
  TradingSignalParams,
} from '@/types/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Reference Data
export const fetchZones = async (): Promise<Zone[]> => {
  const response = await api.get<Zone[]>('/api/zones');
  return response.data;
};

export const fetchInterfaces = async (): Promise<Interface[]> => {
  const response = await api.get<Interface[]>('/api/interfaces');
  return response.data;
};

export const fetchStats = async (): Promise<Stats> => {
  const response = await api.get<Stats>('/api/stats');
  return response.data;
};

// Map Data
export const fetchZoneBoundaries = async (): Promise<any> => {
  // Add cache-busting parameter to ensure fresh data
  const response = await api.get('/api/maps/nyiso-zones', {
    params: {
      _t: Date.now(), // Cache buster
    },
    headers: {
      'Cache-Control': 'no-cache',
    },
  });
  return response.data;
};

// Priority 1 - Core Trading Data
export const fetchMarketAdvisories = async (params?: DateRangeParams): Promise<MarketAdvisory[]> => {
  const response = await api.get<MarketAdvisory[]>('/api/market-advisories', { params });
  return response.data;
};

export const fetchConstraints = async (params?: ConstraintParams): Promise<Constraint[]> => {
  const response = await api.get<Constraint[]>('/api/constraints', { params });
  return response.data;
};

export const fetchTimeWeightedLBMP = async (params?: ZoneFilterParams): Promise<TimeWeightedLBMP[]> => {
  const response = await api.get<TimeWeightedLBMP[]>('/api/timeweighted-lbmp', { params });
  return response.data;
};

export const fetchAncillaryServices = async (params?: AncillaryServiceParams): Promise<AncillaryService[]> => {
  const response = await api.get<AncillaryService[]>('/api/ancillary-services', { params });
  return response.data;
};

// Priority 2 - Market Intelligence
export const fetchExternalRTOPrices = async (params?: DateRangeParams & { rto_name?: string }): Promise<ExternalRTOPrice[]> => {
  const response = await api.get<ExternalRTOPrice[]>('/api/external-rto-prices', { params });
  return response.data;
};

export const fetchATCTTC = async (params?: DateRangeParams & { interfaces?: string; forecast_type?: string }): Promise<ATCTTC[]> => {
  const response = await api.get<ATCTTC[]>('/api/atc-ttc', { params });
  return response.data;
};

export const fetchOutages = async (params?: DateRangeParams & { 
  outage_type?: string; 
  market_type?: string; 
  resource_type?: string;
}): Promise<Outage[]> => {
  const response = await api.get<Outage[]>('/api/outages', { params });
  return response.data;
};

export const fetchWeatherForecast = async (params?: WeatherForecastParams): Promise<WeatherForecast[]> => {
  const response = await api.get<WeatherForecast[]>('/api/weather-forecast', { params });
  return response.data;
};

export const fetchCurrentWeather = async (params?: {
  location?: string;
  zone_name?: string;
  data_source?: 'NYISO' | 'OpenMeteo';
}): Promise<WeatherForecast[]> => {
  const response = await api.get<WeatherForecast[]>('/api/weather-current', { 
    params: params || {} 
  });
  return response.data;
};

export const fetchFuelMix = async (params?: DateRangeParams & { fuel_type?: string }): Promise<FuelMix[]> => {
  const response = await api.get<FuelMix[]>('/api/fuel-mix', { params });
  return response.data;
};

// Existing Core Data
export const fetchRealTimeLBMP = async (params?: ZoneFilterParams): Promise<RealTimeLBMP[]> => {
  const response = await api.get<RealTimeLBMP[]>('/api/realtime-lbmp', { params });
  return response.data;
};

export const fetchDayAheadLBMP = async (params?: ZoneFilterParams): Promise<DayAheadLBMP[]> => {
  const response = await api.get<DayAheadLBMP[]>('/api/dayahead-lbmp', { params });
  return response.data;
};

export const fetchRealTimeLoad = async (params?: ZoneFilterParams): Promise<RealTimeLoad[]> => {
  const response = await api.get<RealTimeLoad[]>('/api/realtime-load', { params });
  return response.data;
};

export const fetchLoadForecast = async (params?: ZoneFilterParams): Promise<LoadForecast[]> => {
  const response = await api.get<LoadForecast[]>('/api/load-forecast', { params });
  return response.data;
};

export const fetchInterfaceFlows = async (params?: DateRangeParams & { interfaces?: string }): Promise<InterfaceFlow[]> => {
  const response = await api.get<InterfaceFlow[]>('/api/interface-flows', { params });
  return response.data;
};

export const fetchInterregionalFlows = async (params?: DateRangeParams): Promise<InterregionalFlow[]> => {
  const response = await api.get<InterregionalFlow[]>('/api/interregional-flows', { params });
  return response.data;
};

// Priority 3 - Calculated Metrics
export const fetchRTDASpreads = async (params?: RTDASpreadParams): Promise<RTDASpread[]> => {
  const response = await api.get<RTDASpread[]>('/api/rt-da-spreads', { params });
  return response.data;
};

export const fetchZoneSpreads = async (params?: DateRangeParams & { include_all_zones?: boolean }): Promise<ZoneSpread[]> => {
  const response = await api.get<ZoneSpread[]>('/api/zone-spreads', { params });
  return response.data;
};

export const fetchLoadForecastErrors = async (params?: LoadForecastErrorParams): Promise<LoadForecastError[]> => {
  const response = await api.get<LoadForecastError[]>('/api/load-forecast-errors', { params });
  return response.data;
};

export const fetchReserveMargins = async (params?: DateRangeParams): Promise<ReserveMargin[]> => {
  const response = await api.get<ReserveMargin[]>('/api/reserve-margins', { params });
  return response.data;
};

export const fetchPriceVolatility = async (params?: PriceVolatilityParams): Promise<PriceVolatility[]> => {
  const response = await api.get<PriceVolatility[]>('/api/price-volatility', { params });
  return response.data;
};

export const fetchCorrelations = async (params?: CorrelationParams): Promise<Correlation[]> => {
  const response = await api.get<Correlation[]>('/api/correlations', { params });
  return response.data;
};

export const fetchTradingSignals = async (params?: TradingSignalParams): Promise<TradingSignal[]> => {
  const response = await api.get<TradingSignal[]>('/api/trading-signals', { params });
  return response.data;
};

export default api;

