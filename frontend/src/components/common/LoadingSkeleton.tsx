/**
 * Loading Skeleton Component
 * Provides skeleton screens for better loading UX
 * Shows structure while content loads
 */

interface LoadingSkeletonProps {
  type?: 'text' | 'card' | 'chart' | 'table' | 'custom';
  lines?: number;
  height?: string;
  className?: string;
}

export const LoadingSkeleton = ({
  type = 'card',
  lines = 3,
  height,
  className = '',
}: LoadingSkeletonProps) => {
  if (type === 'text') {
    return (
      <div className={`animate-pulse ${className}`}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`h-4 bg-slate-700 rounded mb-2 ${
              i === lines - 1 ? 'w-3/4' : 'w-full'
            }`}
          />
        ))}
      </div>
    );
  }

  if (type === 'card') {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-6 bg-slate-700 rounded w-1/3 mb-4" />
        <div className="h-4 bg-slate-700 rounded w-full mb-2" />
        <div className="h-4 bg-slate-700 rounded w-5/6 mb-2" />
        <div className="h-4 bg-slate-700 rounded w-4/6" />
      </div>
    );
  }

  if (type === 'chart') {
    return (
      <div
        className={`animate-pulse bg-slate-700 rounded ${className}`}
        style={{ height: height || '320px' }}
      />
    );
  }

  if (type === 'table') {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-10 bg-slate-700 rounded mb-2" />
        {Array.from({ length: lines }).map((_, i) => (
          <div key={i} className="h-12 bg-slate-700 rounded mb-2" />
        ))}
      </div>
    );
  }

  // Custom type - just return a simple skeleton
  return (
    <div
      className={`animate-pulse bg-slate-700 rounded ${className}`}
      style={{ height: height || '100px' }}
    />
  );
};

