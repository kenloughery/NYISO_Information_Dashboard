/**
 * Enhanced Card Component
 * Improved card design with shadows, hover effects, and optional gradients
 * Can be used as a drop-in replacement for existing card divs
 */

import type { ReactNode } from 'react';

interface EnhancedCardProps {
  children: ReactNode;
  title?: string;
  gradient?: boolean;
  highlight?: boolean;
  hover?: boolean;
  className?: string;
  padding?: 'small' | 'medium' | 'large';
}

export const EnhancedCard = ({
  children,
  title,
  gradient = false,
  highlight = false,
  hover = true,
  className = '',
  padding = 'medium',
}: EnhancedCardProps) => {
  const paddingClasses = {
    small: 'p-4',
    medium: 'p-6',
    large: 'p-8',
  };

  return (
    <div
      className={`
        bg-slate-800
        rounded-xl
        ${paddingClasses[padding]}
        border
        ${highlight ? 'border-blue-500/50' : 'border-slate-700/50'}
        shadow-lg
        shadow-black/20
        ${hover ? 'hover:shadow-xl hover:shadow-black/30 hover:border-slate-600 transition-all duration-300' : ''}
        ${gradient ? 'bg-gradient-to-br from-slate-800 to-slate-900' : ''}
        ${className}
      `}
    >
      {title && (
        <h3 className="text-lg font-semibold mb-4 text-slate-100">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
};

