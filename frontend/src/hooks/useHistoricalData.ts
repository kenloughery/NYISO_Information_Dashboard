/**
 * Custom hooks for historical data queries
 */

import { useQuery } from '@tanstack/react-query';
import * as api from '@/services/api';
import type { DateRangeParams, ZoneFilterParams, WeatherForecastParams } from '@/types/api';

// Day-ahead LBMP
export const useDayAheadLBMP = (params?: ZoneFilterParams) => {
  return useQuery({
    queryKey: ['dayahead-lbmp', params],
    queryFn: () => api.fetchDayAheadLBMP(params),
  });
};

// Time-weighted LBMP
export const useTimeWeightedLBMP = (params?: ZoneFilterParams) => {
  return useQuery({
    queryKey: ['timeweighted-lbmp', params],
    queryFn: () => api.fetchTimeWeightedLBMP(params),
  });
};

// Load Forecast
export const useLoadForecast = (params?: ZoneFilterParams) => {
  return useQuery({
    queryKey: ['load-forecast', params],
    queryFn: () => api.fetchLoadForecast(params),
  });
};

// RT-DA Spreads
export const useRTDASpreads = (params?: ZoneFilterParams & { min_spread?: number }) => {
  return useQuery({
    queryKey: ['rt-da-spreads', params],
    queryFn: () => api.fetchRTDASpreads(params),
  });
};

// Zone Spreads
export const useZoneSpreads = (params?: DateRangeParams & { include_all_zones?: boolean }) => {
  return useQuery({
    queryKey: ['zone-spreads', params],
    queryFn: () => api.fetchZoneSpreads(params),
  });
};

// Load Forecast Errors
export const useLoadForecastErrors = (params?: ZoneFilterParams & { max_error_percent?: number }) => {
  return useQuery({
    queryKey: ['load-forecast-errors', params],
    queryFn: () => api.fetchLoadForecastErrors(params),
  });
};

// Reserve Margins
export const useReserveMargins = (params?: DateRangeParams) => {
  return useQuery({
    queryKey: ['reserve-margins', params],
    queryFn: () => api.fetchReserveMargins(params),
  });
};

// Price Volatility
export const usePriceVolatility = (params?: ZoneFilterParams & { window_hours?: number }) => {
  return useQuery({
    queryKey: ['price-volatility', params],
    queryFn: () => api.fetchPriceVolatility(params),
  });
};

// Correlations
export const useCorrelations = (params?: DateRangeParams & { zones?: string | string[] }) => {
  return useQuery({
    queryKey: ['correlations', params],
    queryFn: () => api.fetchCorrelations(params),
  });
};

// Ancillary Services
export const useAncillaryServices = (params?: DateRangeParams & { 
  market_type?: 'realtime' | 'dayahead'; 
  zones?: string | string[]; 
  service_type?: string;
}) => {
  return useQuery({
    queryKey: ['ancillary-services', params],
    queryFn: () => api.fetchAncillaryServices(params),
  });
};

// External RTO Prices
export const useExternalRTOPrices = (params?: DateRangeParams & { rto_name?: string }) => {
  return useQuery({
    queryKey: ['external-rto-prices', params],
    queryFn: () => api.fetchExternalRTOPrices(params),
  });
};

// ATC/TTC
export const useATCTTC = (params?: DateRangeParams & { interfaces?: string; forecast_type?: string }) => {
  return useQuery({
    queryKey: ['atc-ttc', params],
    queryFn: () => api.fetchATCTTC(params),
  });
};

// Outages
export const useOutages = (params?: DateRangeParams & { 
  outage_type?: string; 
  market_type?: string; 
  resource_type?: string;
}) => {
  return useQuery({
    queryKey: ['outages', params],
    queryFn: () => api.fetchOutages(params),
  });
};

// Weather Forecast
export const useWeatherForecast = (params?: WeatherForecastParams) => {
  return useQuery({
    queryKey: ['weather-forecast', params],
    queryFn: () => api.fetchWeatherForecast(params),
  });
};

// Current Weather (most recent actual weather per station)
export const useCurrentWeather = (params?: {
  location?: string;
  zone_name?: string;
  data_source?: 'NYISO' | 'OpenMeteo';
}) => {
  return useQuery({
    queryKey: ['weather-current', params],
    queryFn: () => api.fetchCurrentWeather(params),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
};

// Fuel Mix
export const useFuelMix = (params?: DateRangeParams & { fuel_type?: string }) => {
  return useQuery({
    queryKey: ['fuel-mix', params],
    queryFn: () => api.fetchFuelMix(params),
  });
};

// Reference Data
export const useZones = () => {
  return useQuery({
    queryKey: ['zones'],
    queryFn: api.fetchZones,
    staleTime: Infinity, // Zones don't change often
  });
};

export const useInterfaces = () => {
  return useQuery({
    queryKey: ['interfaces'],
    queryFn: api.fetchInterfaces,
    staleTime: Infinity, // Interfaces don't change often
  });
};

export const useStats = () => {
  return useQuery({
    queryKey: ['stats'],
    queryFn: api.fetchStats,
    refetchInterval: 60 * 60 * 1000, // Refresh every hour
  });
};

// Zone Boundaries (GeoJSON)
export const useZoneBoundaries = () => {
  return useQuery({
    queryKey: ['zone-boundaries', 'v2'], // Version key to force refresh when updated
    queryFn: () => api.fetchZoneBoundaries(),
    staleTime: 0, // Always refetch to get latest polygons
    gcTime: 60 * 60 * 1000, // Keep in cache for 1 hour
  });
};

