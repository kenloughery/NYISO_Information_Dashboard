/**
 * TypeScript types for NYISO API responses
 */

export interface Zone {
  id: number;
  name: string;
  ptid?: number;
  display_name?: string;
}

export interface Interface {
  id: number;
  name: string;
  point_id?: number;
}

export interface RealTimeLBMP {
  timestamp: string;
  zone_name: string;
  lbmp: number;
  marginal_cost_losses?: number;
  marginal_cost_congestion?: number;
}

export interface DayAheadLBMP {
  timestamp: string;
  zone_name: string;
  lbmp: number;
  marginal_cost_losses?: number;
  marginal_cost_congestion?: number;
}

export interface TimeWeightedLBMP {
  timestamp: string;
  zone_name: string;
  lbmp: number;
  marginal_cost_losses?: number;
  marginal_cost_congestion?: number;
}

export interface RealTimeLoad {
  timestamp: string;
  zone_name: string;
  load: number;
  time_zone?: string;
}

export interface LoadForecast {
  timestamp: string;
  zone_name: string;
  forecast_load: number;
}

export interface InterfaceFlow {
  timestamp: string;
  interface_name: string;
  flow_mwh: number;
  positive_limit_mwh?: number;
  negative_limit_mwh?: number;
}

export interface InterregionalFlow {
  timestamp: string;
  interface_name: string;
  region: string;
  node_name: string;
  flow_mw: number;
  direction: 'import' | 'export' | 'zero';
  positive_limit_mw: number;
  negative_limit_mw: number;
  utilization_percent: number | null;
}

export interface MarketAdvisory {
  timestamp: string;
  advisory_type: string;
  title?: string;
  message?: string;
  severity?: string;
}

export interface Constraint {
  timestamp: string;
  constraint_name: string;
  market_type: 'realtime' | 'dayahead';
  shadow_price?: number;
  binding_status?: string;
  limit_mw?: number;
  flow_mw?: number;
}

export interface AncillaryService {
  timestamp: string;
  zone_name: string;
  market_type: 'realtime' | 'dayahead';
  service_type?: string;
  price?: number;
}

export interface ExternalRTOPrice {
  timestamp: string;
  rto_name: string;
  rtc_price?: number;
  cts_price?: number;
  price_difference?: number;
}

export interface ATCTTC {
  timestamp: string;
  interface_name: string;
  forecast_type: 'short_term' | 'long_term';
  atc_mw?: number;
  ttc_mw?: number;
  trm_mw?: number;
  direction?: string;
}

export interface Outage {
  timestamp: string;
  unit_name: string;
  outage_type: 'scheduled' | 'actual' | 'maintenance';
  market_type?: 'realtime' | 'dayahead';
  resource_type?: 'generator' | 'transmission';
  start_time?: string;
  end_time?: string;
  mw_capacity?: number;
  status?: string;
}

export interface WeatherForecast {
  timestamp: string;
  forecast_time?: string;
  location?: string;
  vintage?: string; // 'Actual' or 'Forecast'
  temperature?: number;
  humidity?: number;
  wind_speed?: number;
  wind_direction?: string;
  cloud_cover_percent?: number;
  zone_name?: string; // NYISO zone name (e.g., "WEST", "N.Y.C.")
  irradiance_w_m2?: number | null; // Solar irradiance in W/m² (Open Meteo only)
  data_source?: string; // "NYISO" or "OpenMeteo"
  forecast_horizon?: number | null;
}

export interface FuelMix {
  timestamp: string;
  fuel_type: string;
  generation_mw: number;
  percentage?: number;
}

// Calculated Metrics
export interface RTDASpread {
  timestamp: string;
  zone_name: string;
  rt_lbmp: number;
  da_lbmp: number;
  spread: number;
  spread_percent: number;
}

export interface ZoneSpread {
  timestamp: string;
  max_zone: string;
  min_zone: string;
  max_price: number;
  min_price: number;
  spread: number;
}

export interface LoadForecastError {
  timestamp: string;
  zone_name: string;
  actual_load: number;
  forecast_load: number;
  error_mw: number;
  error_percent: number;
}

export interface ReserveMargin {
  timestamp: string;
  total_load: number;
  total_generation: number;
  reserve_margin_mw: number;
  reserve_margin_percent: number;
}

export interface PriceVolatility {
  timestamp: string;
  zone_name: string;
  volatility: number;
  mean_price: number;
  std_dev: number;
}

export interface Correlation {
  zone1: string;
  zone2: string;
  correlation: number;
  sample_count: number;
  period_start: string;
  period_end: string;
}

export interface TradingSignal {
  timestamp: string;
  signal_type: string;
  severity: 'info' | 'warning' | 'critical';
  zone_name?: string;
  message: string;
  value?: number;
  threshold?: number;
}

export interface Stats {
  total_records: number;
  date_range: {
    start: string | null;
    end: string | null;
  };
  zones: string[];
  record_counts?: {
    [key: string]: number;
  };
}

// Query Parameters
export interface DateRangeParams {
  start_date?: string;
  end_date?: string;
  limit?: number;
}

export interface WeatherForecastParams extends DateRangeParams {
  location?: string;
  vintage?: 'Actual' | 'Forecast';
  zone_name?: string;
  data_source?: 'NYISO' | 'OpenMeteo';
}

export interface ZoneFilterParams extends DateRangeParams {
  zones?: string | string[];
}

export interface MarketTypeParams extends DateRangeParams {
  market_type?: 'realtime' | 'dayahead';
}

export interface ConstraintParams extends MarketTypeParams {
  constraint_name?: string;
}

export interface AncillaryServiceParams extends MarketTypeParams {
  zones?: string | string[];
  service_type?: string;
}

export interface RTDASpreadParams extends ZoneFilterParams {
  min_spread?: number;
}

export interface LoadForecastErrorParams extends ZoneFilterParams {
  max_error_percent?: number;
}

export interface PriceVolatilityParams extends ZoneFilterParams {
  window_hours?: number;
}

export interface CorrelationParams extends DateRangeParams {
  zones?: string | string[];
}

export interface TradingSignalParams extends DateRangeParams {
  signal_type?: string;
  severity?: 'info' | 'warning' | 'critical';
}

export interface ConnectionPointData extends InterregionalFlow {
  zone: string;
  nyisoPrice: number;
  externalPrice: number | null;
  priceDifferential: number | null;
  arbitrageOpportunity: boolean;
  importMW: number;
  exportMW: number;
}

