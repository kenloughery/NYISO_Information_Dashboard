/**
 * Responsive Chart Container
 * Wrapper component for charts that ensures proper responsive behavior
 * Uses responsive height for better mobile experience
 */

import type { ReactNode } from 'react';
import { ResponsiveContainer } from 'recharts';

interface ResponsiveChartProps {
  children: ReactNode;
  minHeight?: number;
  className?: string;
}

export const ResponsiveChart = ({
  children,
  minHeight = 320,
  className = '',
}: ResponsiveChartProps) => {
  // ResponsiveContainer needs a parent with a defined height (not just minHeight)
  // Use the minHeight value as the actual height for ResponsiveContainer to work
  return (
    <div
      className={`w-full ${className}`}
      style={{ height: `${minHeight}px` }}
    >
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  );
};

