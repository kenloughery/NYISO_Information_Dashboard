/**
 * Circular Gauge Component
 * Displays a value as a circular progress gauge with customizable colors and thresholds
 */

interface CircularGaugeProps {
  value: number;
  max: number;
  label?: string;
  unit?: string;
  size?: number;
  strokeWidth?: number;
  showPercentage?: boolean;
  thresholds?: {
    low: number;      // Percentage threshold for low (green)
    medium: number;   // Percentage threshold for medium (yellow)
    high: number;     // Percentage threshold for high (red)
  };
  className?: string;
}

export const CircularGauge = ({
  value,
  max,
  label,
  unit,
  size = 120,
  strokeWidth = 12,
  showPercentage = true,
  thresholds = { low: 50, medium: 75, high: 90 },
  className = '',
}: CircularGaugeProps) => {
  const percentage = Math.min((value / max) * 100, 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  // Determine color based on percentage and thresholds
  // For accuracy metrics (0-100%), higher is better
  // For utilization metrics, thresholds work differently
  const getColor = () => {
    // If max is 100, assume this is a percentage metric where higher is better (like accuracy)
    if (max === 100) {
      if (percentage >= thresholds.high) return '#10b981'; // Green (excellent)
      if (percentage >= thresholds.medium) return '#3b82f6'; // Blue (good)
      if (percentage >= thresholds.low) return '#f59e0b'; // Orange (warning)
      return '#ef4444'; // Red (poor)
    }
    // For other metrics (like utilization), use standard thresholds
    if (percentage >= thresholds.high) return '#ef4444'; // Red
    if (percentage >= thresholds.medium) return '#f59e0b'; // Orange
    if (percentage >= thresholds.low) return '#3b82f6'; // Blue
    return '#10b981'; // Green
  };

  const color = getColor();

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#1e293b"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-2xl font-bold text-slate-100">
            {value.toLocaleString()}
          </div>
          {unit && (
            <div className="text-xs text-slate-400 mt-0.5">{unit}</div>
          )}
          {showPercentage && (
            <div className="text-xs text-slate-500 mt-1">
              {percentage.toFixed(0)}%
            </div>
          )}
        </div>
      </div>
      {label && (
        <div className="mt-2 text-sm font-medium text-slate-300 text-center">
          {label}
        </div>
      )}
    </div>
  );
};

