/**
 * Application configuration constants
 */

// In production (served from same origin), use empty string for relative URLs
// In development, use localhost:8000 or the VITE_API_BASE_URL env var
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.PROD ? '' : 'http://localhost:8000');

export const REFRESH_INTERVALS = {
  REAL_TIME: 5 * 60 * 1000, // 5 minutes
  HOURLY: 60 * 60 * 1000, // 1 hour
  DAILY: 24 * 60 * 60 * 1000, // 24 hours
} as const;

export const NYISO_ZONES = [
  'CAPITL',
  'CENTRL',
  'DUNWOD',
  'GENESE',
  'HUD VL',
  'LONGIL',
  'MILLWD',
  'N.Y.C.',
  'NORTH',
  'WEST',
  'MHK VL',
] as const;

export const TRADING_SIGNAL_TYPES = [
  'rt_da_spread',
  'load_forecast_error',
  'low_reserve_margin',
  'high_volatility',
  'constraint_alert',
] as const;

export const SEVERITY_LEVELS = ['info', 'warning', 'critical'] as const;

