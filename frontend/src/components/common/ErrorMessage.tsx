/**
 * Enhanced Error message component with accessibility
 */

import { Warning } from '@mui/icons-material';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  title?: string;
  className?: string;
}

export const ErrorMessage = ({ 
  message, 
  onRetry, 
  title = 'Error',
  className = '' 
}: ErrorMessageProps) => {
  return (
    <div 
      className={`bg-red-900/30 border border-red-700/50 rounded-lg p-4 ${className}`}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="flex items-start gap-3">
        <Warning className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <h3 className="text-red-400 font-semibold mb-1">{title}</h3>
          <p className="text-red-300 text-sm">{message}</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-red-700 hover:bg-red-600 rounded-lg transition-colors text-sm font-medium text-white flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-slate-900"
            aria-label="Retry loading data"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
};

