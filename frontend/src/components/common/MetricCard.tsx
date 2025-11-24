/**
 * Metric Card Component
 * Specialized card for displaying key metrics with optional gradients and icons
 */

import type { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
  gradient?: boolean;
  highlight?: boolean;
  icon?: ReactNode;
  subtitle?: string;
  className?: string;
}

export const MetricCard = ({
  label,
  value,
  unit,
  trend,
  gradient = false,
  highlight = false,
  icon,
  subtitle,
  className = '',
}: MetricCardProps) => {
  const trendColors = {
    up: 'text-green-400',
    down: 'text-red-400',
    neutral: 'text-slate-400',
  };

  const trendIcons = {
    up: '↑',
    down: '↓',
    neutral: '→',
  };

  return (
    <div
      className={`
        bg-slate-800
        rounded-xl
        p-6
        border
        ${highlight ? 'border-blue-500/50' : 'border-slate-700/50'}
        shadow-lg
        shadow-black/20
        hover:shadow-xl
        hover:shadow-black/30
        hover:border-slate-600
        transition-all
        duration-300
        ${gradient ? 'bg-gradient-to-br from-slate-800 to-slate-900' : ''}
        ${className}
      `}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="text-sm text-slate-400 font-medium">{label}</div>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      
      <div className="flex items-baseline gap-2">
        <div className="text-3xl font-bold text-slate-100">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
        {unit && (
          <div className="text-lg text-slate-400 font-medium">{unit}</div>
        )}
        {trend && (
          <div className={`text-sm font-semibold ${trendColors[trend]}`}>
            {trendIcons[trend]}
          </div>
        )}
      </div>
      
      {subtitle && (
        <div className="text-xs text-slate-500 mt-1">{subtitle}</div>
      )}
    </div>
  );
};

