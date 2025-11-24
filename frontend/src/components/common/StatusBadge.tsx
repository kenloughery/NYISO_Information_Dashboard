/**
 * Status Badge Component
 * Color-coded badge for displaying status information
 */

interface StatusBadgeProps {
  label: string;
  status: 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const StatusBadge = ({
  label,
  status,
  size = 'md',
  className = '',
}: StatusBadgeProps) => {
  const statusColors = {
    success: 'bg-green-500/20 text-green-400 border-green-500/50',
    warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    danger: 'bg-red-500/20 text-red-400 border-red-500/50',
    info: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
    neutral: 'bg-slate-500/20 text-slate-400 border-slate-500/50',
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2',
  };

  return (
    <span
      className={`
        inline-flex
        items-center
        font-semibold
        rounded-lg
        border
        ${statusColors[status]}
        ${sizeClasses[size]}
        ${className}
      `}
    >
      {label}
    </span>
  );
};

