/**
 * Design System - Color Palette
 * Enhanced color system with semantic meanings
 * Extends Tailwind's default colors without replacing them
 */

export const colors = {
  // Status colors (semantic meanings)
  status: {
    success: '#10b981', // Green for normal/positive states
    warning: '#f59e0b', // Amber for warnings
    danger: '#ef4444',  // Red for critical/negative states
    info: '#3b82f6',    // Blue for informational
    neutral: '#6b7280', // Gray for neutral states
  },

  // Price indicators
  price: {
    low: '#10b981',     // Green for low prices
    medium: '#f59e0b',  // Amber for medium prices
    high: '#ef4444',    // Red for high prices
    veryHigh: '#dc2626', // Dark red for very high prices
  },

  // Background gradients
  gradient: {
    primary: 'from-blue-600 to-purple-600',
    secondary: 'from-slate-800 to-slate-900',
    success: 'from-green-600 to-emerald-600',
    warning: 'from-amber-600 to-orange-600',
    danger: 'from-red-600 to-rose-600',
  },

  // Accent colors
  accent: {
    primary: '#8b5cf6',   // Purple for highlights
    secondary: '#3b82f6', // Blue for secondary highlights
    tertiary: '#10b981',  // Green for tertiary highlights
  },

  // Chart colors (for data visualization)
  chart: {
    primary: '#3b82f6',   // Blue
    secondary: '#8b5cf6', // Purple
    success: '#10b981',   // Green
    warning: '#f59e0b',   // Amber
    danger: '#ef4444',    // Red
    info: '#06b6d4',      // Cyan
    neutral: '#6b7280',   // Gray
  },

  // Background colors (extending slate palette)
  background: {
    base: '#0f172a',      // slate-900
    card: '#1e293b',      // slate-800
    cardHover: '#334155', // slate-700
    overlay: 'rgba(0, 0, 0, 0.5)',
  },

  // Border colors
  border: {
    default: '#334155',   // slate-700
    light: '#475569',     // slate-600
    dark: '#1e293b',      // slate-800
    accent: '#8b5cf6',     // Purple accent
  },

  // Text colors
  text: {
    primary: '#f1f5f9',   // slate-100
    secondary: '#cbd5e1', // slate-300
    tertiary: '#94a3b8',  // slate-400
    muted: '#64748b',     // slate-500
  },
} as const;

/**
 * Get color by semantic name
 * Useful for programmatic color selection
 */
export const getColor = (category: keyof typeof colors, key: string): string => {
  const categoryColors = colors[category] as Record<string, string>;
  return categoryColors[key] || categoryColors[Object.keys(categoryColors)[0]] || '#000000';
};

/**
 * Get status color based on value thresholds
 */
export const getStatusColor = (value: number, thresholds: { low: number; medium: number; high: number }): string => {
  if (value >= thresholds.high) return colors.status.danger;
  if (value >= thresholds.medium) return colors.status.warning;
  return colors.status.success;
};

/**
 * Get price color based on price value
 */
export const getPriceColor = (price: number, thresholds: { low: number; medium: number; high: number }): string => {
  if (price >= thresholds.high) return colors.price.high;
  if (price >= thresholds.medium) return colors.price.medium;
  return colors.price.low;
};

