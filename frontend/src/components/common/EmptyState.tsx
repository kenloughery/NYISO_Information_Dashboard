/**
 * Empty State Component
 * Displays helpful empty states when no data is available
 */

interface EmptyStateProps {
  title?: string;
  message?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  icon?: React.ReactNode;
  className?: string;
}

export const EmptyState = ({
  title = 'No Data Available',
  message = 'There is no data to display at this time.',
  action,
  icon,
  className = '',
}: EmptyStateProps) => {
  return (
    <div
      className={`
        flex
        flex-col
        items-center
        justify-center
        py-12
        px-4
        text-center
        ${className}
      `}
    >
      {icon && (
        <div className="text-slate-500 mb-4 text-4xl">{icon}</div>
      )}
      
      <h3 className="text-lg font-semibold text-slate-300 mb-2">
        {title}
      </h3>
      
      <p className="text-sm text-slate-400 mb-6 max-w-md">
        {message}
      </p>
      
      {action && (
        <button
          onClick={action.onClick}
          className="
            px-4
            py-2
            bg-blue-600
            hover:bg-blue-700
            text-white
            font-medium
            rounded-lg
            transition-colors
          "
        >
          {action.label}
        </button>
      )}
    </div>
  );
};

